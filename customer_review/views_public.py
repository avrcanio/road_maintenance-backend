import json
from typing import Any, Dict, Optional

from django.contrib.gis.gdal import GDALException
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views import View

from .models import CustomerReview, CustomerReviewDecision, ReviewToken


def _ip(req) -> Optional[str]:
    return req.META.get("REMOTE_ADDR")


def _ua(req) -> str:
    return req.META.get("HTTP_USER_AGENT", "")[:512]


def _geom_to_geojson_4326_or_none(geom) -> Optional[Dict[str, Any]]:
    if not geom:
        return None
    g = geom.clone()
    try:
        g.transform(4326)
    except GDALException:
        return None
    return json.loads(g.geojson)


def _validate_active_token_or_error(token: ReviewToken):
    if token.revoked_at:
        return 403, {"code": "TOKEN_REVOKED", "detail": "Ovaj link je opozvan."}
    if token.used_at:
        return 410, {"code": "TOKEN_USED", "detail": "Ovaj link je već iskorišten."}
    if timezone.now() >= token.expires_at:
        return 410, {"code": "TOKEN_EXPIRED", "detail": "Ovaj link je istekao."}
    if token.scope != "workitem:review":
        return 403, {"code": "SCOPE_MISMATCH", "detail": "Ovaj link nije važeći za ovu radnju."}
    return None


class CustomerReviewPublicView(View):
    def get(self, request, jti: str):
        token = get_object_or_404(ReviewToken, jti=jti)
        err = _validate_active_token_or_error(token)
        if err:
            code, payload = err
            return JsonResponse(payload, status=code)

        review: CustomerReview = token.customer_review
        wi = review.work_item

        route_line = getattr(wi, "route_line", None) or getattr(wi, "geom", None)
        processed_polygon = getattr(wi, "processed_polygon", None)

        payload = {
            "review": {
                "id": review.id,
                "version": review.version,
                "status": review.status,
                "deadline": review.deadline.isoformat() if review.deadline else None,
                "note_public": review.note_public or "",
            },
            "work_item": {
                "id": wi.id,
                "label": getattr(wi, "name", None)
                or getattr(wi, "title", None)
                or f"WorkItem #{wi.id}",
                "operation_type": getattr(wi, "operation_type_id", None),
                "quantity": getattr(wi, "quantity", None),
                "unit": getattr(wi, "unit", None),
                "date_performed": (
                    getattr(wi, "performed_at", None).isoformat()
                    if getattr(wi, "performed_at", None)
                    else None
                ),
            },
            "geometry": {
                "route_line": _geom_to_geojson_4326_or_none(route_line),
                "processed_polygon": _geom_to_geojson_4326_or_none(processed_polygon),
            },
            "allowed_actions": ["accepted", "change_requested"],
            "requires": {
                "comment_if_change_requested": True,
                "geom_if_change_requested": False,
            },
            "data_snapshot_hash": review.data_snapshot_hash or "",
            "ui": {
                "deadline_hint": "Molimo potvrdite do navedenog roka.",
            },
        }
        return JsonResponse(payload, status=200)

    @transaction.atomic
    def post(self, request, jti: str):
        token = (
            ReviewToken.objects.select_for_update()
            .filter(jti=jti)
            .first()
        )
        if not token:
            return JsonResponse(
                {"code": "NOT_FOUND", "detail": "Nepoznat token."},
                status=404,
            )

        err = _validate_active_token_or_error(token)
        if err:
            code, payload = err
            return JsonResponse(payload, status=code)

        review: CustomerReview = token.customer_review
        wi = review.work_item

        try:
            if request.content_type == "application/json" and request.body:
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = request.POST.dict()
        except Exception:
            return JsonResponse(
                {"code": "BAD_JSON", "detail": "Neispravan JSON."},
                status=400,
            )

        action = (data.get("action") or "").strip()
        comment = (data.get("comment") or "").strip()
        client_hash = (data.get("data_snapshot_hash") or "").strip()
        geom_geojson = data.get("geom")

        if not client_hash or client_hash != (review.data_snapshot_hash or ""):
            return JsonResponse(
                {
                    "code": "SNAPSHOT_OUTDATED",
                    "detail": "Podaci su se promijenili. Osvježite stranicu.",
                },
                status=409,
            )

        if action not in ("accepted", "change_requested"):
            return JsonResponse(
                {"code": "ACTION_INVALID", "detail": "Nepodržana akcija."},
                status=422,
            )

        if action == "change_requested" and not comment:
            return JsonResponse(
                {
                    "code": "COMMENT_REQUIRED",
                    "detail": "Komentar je obavezan za traženje dorade.",
                },
                status=422,
            )

        decision_geom = None
        if geom_geojson:
            try:
                geos = GEOSGeometry(json.dumps(geom_geojson), srid=4326)
                geos.transform(3765)
                decision_geom = geos
            except Exception:
                return JsonResponse(
                    {"code": "GEOM_INVALID", "detail": "Neispravan GeoJSON."},
                    status=422,
                )

        decision = CustomerReviewDecision.objects.create(
            customer_review=review,
            decided_by_user=token.user,
            action=action,
            comment=comment,
            geom=decision_geom,
            data_snapshot_hash=client_hash,
            ip_address=_ip(request),
            user_agent=_ua(request),
        )

        if action == "accepted":
            review.status = CustomerReview.Status.ACCEPTED
            review.closed_at = timezone.now()
            wi_status = "accepted"
        else:
            review.status = CustomerReview.Status.CHANGE_REQUESTED
            review.closed_at = timezone.now()
            wi_status = "needs_rework"

        review.save(update_fields=["status", "closed_at", "updated_at"])

        if hasattr(wi, "status"):
            setattr(wi, "status", wi_status)
            wi.save(update_fields=["status"])

        token.used_at = timezone.now()
        token.save(update_fields=["used_at"])

        return JsonResponse(
            {
                "result": "ok",
                "review_status": review.status,
                "work_item_status": wi_status,
                "message": "Hvala, zaprimili smo vašu odluku.",
                "decision_id": decision.id,
            },
            status=200,
        )

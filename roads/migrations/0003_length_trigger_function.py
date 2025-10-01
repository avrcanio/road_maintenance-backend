from django.db import migrations

CREATE_FUNCTION = r"""
CREATE OR REPLACE FUNCTION roads_set_length()
RETURNS trigger AS
$$
BEGIN
  IF NEW.geom IS NOT NULL THEN
    NEW.length := round(ST_Length(NEW.geom)::numeric, 0);
  ELSE
    NEW.length := NULL;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

CREATE_TRIGGER = r"""
DROP TRIGGER IF EXISTS roads_roadsection_set_length_biu
  ON public.roads_roadsection;

CREATE TRIGGER roads_roadsection_set_length_biu
BEFORE INSERT OR UPDATE OF geom ON public.roads_roadsection
FOR EACH ROW
EXECUTE FUNCTION roads_set_length();
"""

REVERSE_SQL = r"""
DROP TRIGGER IF EXISTS roads_roadsection_set_length_biu
  ON public.roads_roadsection;

DROP FUNCTION IF EXISTS roads_set_length();
"""

class Migration(migrations.Migration):

    dependencies = [
        ('roads', '0002_alter_roadsection_length'),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_FUNCTION, reverse_sql="DROP FUNCTION IF EXISTS roads_set_length();"),
        migrations.RunSQL(sql=CREATE_TRIGGER, reverse_sql="""
            DROP TRIGGER IF EXISTS roads_roadsection_set_length_biu
            ON public.roads_roadsection;
        """),
        # NEMA backfill-a jer je već odrađen u Navicatu
    ]

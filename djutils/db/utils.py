from django.conf import settings
from django.db import connection
from django.db.models.query import QuerySet


def extract_rel_field(model, related_to):
    """
    Given a model, extra the name of the field that rels to a user
    see: django-relationships
    """
    for field in model._meta.fields + model._meta.many_to_many:
        if field.rel and field.rel.to == related_to:
            return field.name
    for rel in model._meta.get_all_related_many_to_many_objects():
        if rel.model == related_to:
            return rel.var_name

def get_queryset_position(qs, obj):
    result = None
    
    if 'postgresql_psycopg2' in settings.DATABASES['default']['ENGINE']:
        cursor = connection.cursor()
        
        try:
            cursor.execute('CREATE TEMP sequence temp_seq;')
            
            temp_table_query = """
                CREATE TEMP TABLE ordered_objects AS
                    SELECT nextval('temp_seq') AS row_number, qs.*
                    FROM (""" + str(qs.query) + ') AS qs;'
            
            obj_lookup_query = """
                SELECT row_number
                FROM ordered_objects
                WHERE """ + qs.model._meta.pk.attname + '=%s;'

            cursor.execute(temp_table_query)
            cursor.execute(obj_lookup_query, [obj.pk])
            result = cursor.fetchone()[0]
        
        finally:
            cursor.execute('DROP TABLE ordered_objects;')
            cursor.execute('DROP SEQUENCE temp_seq;')
        
        return result
    
    else:
        if isinstance(qs, QuerySet) and qs.query.can_filter():
            pk_list = qs.values_list('pk', flat=True)
        else:
            pk_list = map(lambda o: o.pk, qs)
        
        for (i, pk) in enumerate(pk_list):
            if obj.pk == pk:
                return i + 1

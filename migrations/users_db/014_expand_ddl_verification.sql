-- Несколько независимых проверочных вызовов не позволяют подогнать функцию
-- под единственное входное значение из примера.

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'verification_cases', jsonb_build_array(
        jsonb_build_object(
            'test_query', 'SELECT get_enlistment_age(1);',
            'columns', jsonb_build_array('get_enlistment_age'),
            'data', jsonb_build_array(jsonb_build_array(18)),
            'row_count', 1
        ),
        jsonb_build_object(
            'test_query', 'SELECT get_enlistment_age(2);',
            'columns', jsonb_build_array('get_enlistment_age'),
            'data', jsonb_build_array(jsonb_build_array(17)),
            'row_count', 1
        ),
        jsonb_build_object(
            'test_query', 'SELECT get_enlistment_age(3);',
            'columns', jsonb_build_array('get_enlistment_age'),
            'data', jsonb_build_array(jsonb_build_array(23)),
            'row_count', 1
        )
    )
)
WHERE task_global_id = 106;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'verification_cases', jsonb_build_array(
        jsonb_build_object(
            'test_query',
            'SELECT * FROM get_unit_soldiers(''1-я морская бригада'') ORDER BY full_name;',
            'columns', jsonb_build_array('full_name', 'enlistment_city'),
            'data', jsonb_build_array(
                jsonb_build_array('Волкова Елена Сергеевна', 'Ленинград')
            ),
            'row_count', 1
        ),
        jsonb_build_object(
            'test_query',
            'SELECT * FROM get_unit_soldiers(''316-я стрелковая дивизия'') ORDER BY full_name;',
            'columns', jsonb_build_array('full_name', 'enlistment_city'),
            'data', jsonb_build_array(
                jsonb_build_array('Иванов Алексей Петрович', 'Москва')
            ),
            'row_count', 1
        )
    )
)
WHERE task_global_id = 107;

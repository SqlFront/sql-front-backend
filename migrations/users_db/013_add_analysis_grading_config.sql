-- Явные требования, схема и политика качества для реальных учебных заданий.
-- Конфигурация хранится рядом с expected_result и читается анализатором без
-- добавления новых столбцов в таблицу tasks.

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_tables', jsonb_build_array('soldier'),
        'required_selected_columns', jsonb_build_array('full_name', 'birth_year')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'soldier', jsonb_build_array(
                'id', 'full_name', 'birth_year', 'gender', 'rank', 'branch',
                'enlistment_city', 'status', 'enlistment_date'
            )
        )
    ),
    'quality_policy', jsonb_build_object('max_penalty_rate', 0.20)
)
WHERE task_global_id = 1;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_tables', jsonb_build_array('battle'),
        'required_selected_columns', jsonb_build_array('battle_name')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'battle', jsonb_build_array(
                'id', 'battle_name', 'start_date', 'end_date', 'location',
                'result', 'importance_level'
            )
        )
    )
)
WHERE task_global_id = 2;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_features', jsonb_build_array('order_by'),
        'required_tables', jsonb_build_array('battle'),
        'required_selected_columns', jsonb_build_array(
            'battle_name', 'start_date', 'end_date', 'location'
        )
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'battle', jsonb_build_array(
                'id', 'battle_name', 'start_date', 'end_date', 'location',
                'result', 'importance_level'
            )
        )
    ),
    'quality_policy', jsonb_build_object(
        'penalty_rates', jsonb_build_object('style.order_by_ordinal', 0.10)
    )
)
WHERE task_global_id = 5;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_features', jsonb_build_array('join'),
        'required_tables', jsonb_build_array('soldier', 'soldier_medal', 'medal'),
        'required_selected_columns', jsonb_build_array('full_name', 'medal_name')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'soldier', jsonb_build_array(
                'id', 'full_name', 'birth_year', 'gender', 'rank', 'branch',
                'enlistment_city', 'status', 'enlistment_date'
            ),
            'soldier_medal', jsonb_build_array('soldier_id', 'medal_id', 'award_date'),
            'medal', jsonb_build_array('id', 'medal_name', 'establishment_date', 'award_criteria')
        )
    ),
    'quality_policy', jsonb_build_object('max_penalty_rate', 0.25)
)
WHERE task_global_id = 6;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_tables', jsonb_build_array('military_unit'),
        'required_selected_columns', jsonb_build_array('unit_name')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'military_unit', jsonb_build_array(
                'id', 'unit_name', 'unit_type', 'location', 'formation_date',
                'combat_efficiency'
            )
        )
    )
)
WHERE task_global_id = 8;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_tables', jsonb_build_array('equipment'),
        'required_selected_columns', jsonb_build_array('item_name')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'equipment', jsonb_build_array(
                'id', 'unit_id', 'equipment_type', 'item_name', 'quantity',
                'last_replenishment'
            )
        )
    )
)
WHERE task_global_id = 9;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_tables', jsonb_build_array('battle'),
        'required_selected_columns', jsonb_build_array('battle_name')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'battle', jsonb_build_array(
                'id', 'battle_name', 'start_date', 'end_date', 'location',
                'result', 'importance_level'
            )
        )
    )
)
WHERE task_global_id = 13;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_features', jsonb_build_array('aggregate_function'),
        'required_tables', jsonb_build_array('soldier'),
        'required_functions', jsonb_build_array('avg'),
        'required_output_aliases', jsonb_build_array('average_age')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'soldier', jsonb_build_array(
                'id', 'full_name', 'birth_year', 'gender', 'rank', 'branch',
                'enlistment_city', 'status', 'enlistment_date'
            )
        )
    )
)
WHERE task_global_id = 15;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_features', jsonb_build_array('aggregate_function'),
        'required_tables', jsonb_build_array('soldier'),
        'required_functions', jsonb_build_array('count')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'soldier', jsonb_build_array(
                'id', 'full_name', 'birth_year', 'gender', 'rank', 'branch',
                'enlistment_city', 'status', 'enlistment_date'
            )
        )
    )
)
WHERE task_global_id = 18;

UPDATE public.tasks
SET expected_result = expected_result || jsonb_build_object(
    'analysis_requirements', jsonb_build_object(
        'required_features', jsonb_build_array('subquery'),
        'required_tables', jsonb_build_array('military_unit', 'equipment'),
        'required_selected_columns', jsonb_build_array('unit_name')
    ),
    'analysis_context', jsonb_build_object(
        'strict_schema', true,
        'schema', jsonb_build_object(
            'military_unit', jsonb_build_array(
                'id', 'unit_name', 'unit_type', 'location', 'formation_date',
                'combat_efficiency'
            ),
            'equipment', jsonb_build_array(
                'id', 'unit_id', 'equipment_type', 'item_name', 'quantity',
                'last_replenishment'
            )
        )
    ),
    'quality_policy', jsonb_build_object(
        'max_penalty_rate', 0.30,
        'grade_thresholds', jsonb_build_object('good', 0.80, 'excellent', 0.95)
    )
)
WHERE task_global_id = 30;

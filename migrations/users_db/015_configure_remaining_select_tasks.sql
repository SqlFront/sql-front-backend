-- Индивидуальные требования анализа для оставшихся SELECT-заданий миссий 0-2.
-- Схемы таблиц берутся приложением из общего каталога GAME_ANALYSIS_SCHEMA.

WITH task_config(
    task_global_id,
    tables,
    features,
    functions,
    selected_columns,
    output_aliases
) AS (
    VALUES
    -- Миссия 0: базовые SELECT-задания.
    (4,  ARRAY['military_service'], ARRAY['subquery','group_by','aggregate_function'], ARRAY['count'], ARRAY[]::text[], ARRAY['answer']),
    (7,  ARRAY['soldier'], ARRAY[]::text[], ARRAY[]::text[], ARRAY['full_name'], ARRAY[]::text[]),
    (10, ARRAY['soldier'], ARRAY[]::text[], ARRAY[]::text[], ARRAY['full_name'], ARRAY[]::text[]),
    (11, ARRAY['military_unit'], ARRAY[]::text[], ARRAY[]::text[], ARRAY['unit_name'], ARRAY[]::text[]),
    (12, ARRAY['equipment'], ARRAY[]::text[], ARRAY[]::text[], ARRAY['item_name'], ARRAY[]::text[]),
    (14, ARRAY['military_unit','military_service'], ARRAY['join','group_by','order_by','aggregate_function'], ARRAY['count'], ARRAY['unit_name'], ARRAY['total_soldiers']),
    (3,  ARRAY['equipment'], ARRAY['group_by','aggregate_function'], ARRAY['sum'], ARRAY['equipment_type'], ARRAY['total']),
    (16, ARRAY['military_unit'], ARRAY['aggregate_function'], ARRAY['min','max'], ARRAY['formation_date'], ARRAY[]::text[]),
    (17, ARRAY['soldier'], ARRAY[]::text[], ARRAY[]::text[], ARRAY['full_name','rank'], ARRAY['soldier_info']),
    (19, ARRAY['military_unit'], ARRAY['group_by','aggregate_function'], ARRAY['avg'], ARRAY['unit_type'], ARRAY['avg_efficiency']),
    (20, ARRAY['soldier'], ARRAY['group_by','aggregate_function'], ARRAY['count'], ARRAY['status'], ARRAY[]::text[]),
    (21, ARRAY['military_unit'], ARRAY['group_by','aggregate_function'], ARRAY['variance'], ARRAY['unit_type'], ARRAY['variance']),
    (22, ARRAY['military_unit'], ARRAY[]::text[], ARRAY[]::text[], ARRAY['unit_name','combat_efficiency'], ARRAY['efficiency_category']),
    (23, ARRAY['battle'], ARRAY['group_by','order_by','aggregate_function'], ARRAY['extract','count'], ARRAY['start_date'], ARRAY['year','battles_count']),
    (24, ARRAY['soldier'], ARRAY[]::text[], ARRAY[]::text[], ARRAY['full_name','birth_year','enlistment_date'], ARRAY['enlistment_age']),
    (25, ARRAY['military_unit','military_service','soldier'], ARRAY['join','group_by','order_by','aggregate_function'], ARRAY['min','max'], ARRAY['unit_name','birth_year','enlistment_date'], ARRAY[]::text[]),
    (26, ARRAY['soldier'], ARRAY['group_by','order_by','aggregate_function'], ARRAY['avg','round'], ARRAY['enlistment_city','birth_year','enlistment_date'], ARRAY['avg_age']),
    (27, ARRAY['battle'], ARRAY['group_by'], ARRAY[]::text[], ARRAY['battle_name','start_date','end_date'], ARRAY['duration_days']),
    (28, ARRAY['military_unit'], ARRAY['group_by','order_by','aggregate_function'], ARRAY['extract','count'], ARRAY['formation_date'], ARRAY['formation_year','units_count']),
    (29, ARRAY['military_unit','military_service','soldier'], ARRAY['join','group_by','aggregate_function'], ARRAY['max'], ARRAY['unit_name','birth_year'], ARRAY['youngest_birth_year']),
    (31, ARRAY['soldier','military_service'], ARRAY['subquery'], ARRAY[]::text[], ARRAY['full_name','birth_year'], ARRAY[]::text[]),
    (34, ARRAY['enemy_unit'], ARRAY['except','order_by'], ARRAY[]::text[], ARRAY['unit_name'], ARRAY[]::text[]),

    -- Миссия 1: составные запросы и аналитические конструкции.
    (37, ARRAY['equipment','military_unit'], ARRAY['subquery','window_function','aggregate_function'], ARRAY['sum'], ARRAY['unit_id','quantity'], ARRAY['total_ammo']),
    (63, ARRAY['equipment','military_unit'], ARRAY['cte','join','group_by','aggregate_function'], ARRAY['sum'], ARRAY['unit_name','quantity','equipment_type'], ARRAY['ammunition_total','medicine_total']),
    (38, ARRAY['soldier','military_service','military_unit','battle'], ARRAY['join','group_by','window_function','order_by','limit','aggregate_function'], ARRAY['count','rank'], ARRAY['full_name'], ARRAY['battles_participated','hero_rank']),
    (39, ARRAY['soldier','military_service','military_unit'], ARRAY['cte','join','group_by','aggregate_function'], ARRAY['count'], ARRAY['unit_name','combat_efficiency','status'], ARRAY['initial_efficiency','loss_percentage','adjusted_efficiency']),
    (40, ARRAY['military_unit','equipment'], ARRAY['join','group_by','window_function','aggregate_function'], ARRAY['sum','rank'], ARRAY['unit_name','equipment_type','quantity'], ARRAY['total','supply_rank']),
    (64, ARRAY['military_unit','equipment'], ARRAY['join','group_by','aggregate_function'], ARRAY['sum','group_concat'], ARRAY['equipment_type','quantity','item_name'], ARRAY['total','items']),
    (75, ARRAY['soldier','military_service','military_unit'], ARRAY['join','window_function'], ARRAY['first_value','last_value'], ARRAY['unit_name','full_name'], ARRAY['first_enlisted','last_enlisted']),
    (77, ARRAY['soldier','military_service','military_unit'], ARRAY['join','order_by'], ARRAY[]::text[], ARRAY['full_name','unit_name','start_date'], ARRAY[]::text[]),
    (41, ARRAY['equipment','military_unit','military_service'], ARRAY['join','group_by','aggregate_function'], ARRAY['sum','count','round'], ARRAY['equipment_type','quantity'], ARRAY['total','per_soldier']),
    (67, ARRAY['soldier','equipment_assignment'], ARRAY['join','subquery'], ARRAY[]::text[], ARRAY['full_name'], ARRAY[]::text[]),
    (69, ARRAY['soldier'], ARRAY['group_by','order_by','aggregate_function'], ARRAY['count'], ARRAY['birth_year'], ARRAY['age_group','quantity']),
    (76, ARRAY['soldier'], ARRAY['cte','group_by','window_function','aggregate_function'], ARRAY['count','avg'], ARRAY['enlistment_date','status'], ARRAY['month','killed','moving_avg']),
    (70, ARRAY['military_unit','military_service'], ARRAY['join','group_by','order_by','aggregate_function'], ARRAY['count'], ARRAY['unit_name'], ARRAY['total_soldiers']),
    (54, ARRAY['military_unit','equipment'], ARRAY['join','window_function','aggregate_function'], ARRAY['sum'], ARRAY['unit_name','last_replenishment','quantity'], ARRAY['cumulative_ammo']),
    (71, ARRAY['soldier'], ARRAY['join','order_by'], ARRAY[]::text[], ARRAY['full_name','enlistment_city'], ARRAY['soldier_name1','soldier_name2','common_city']),
    (43, ARRAY['soldier','military_service','military_unit'], ARRAY['join','group_by','order_by','aggregate_function'], ARRAY['sum'], ARRAY['unit_name','gender'], ARRAY['military_unit_name']),
    (44, ARRAY['soldier','military_service','military_unit','battle'], ARRAY['subquery'], ARRAY[]::text[], ARRAY['full_name'], ARRAY[]::text[]),
    (72, ARRAY['soldier','military_service','military_unit'], ARRAY['union','subquery'], ARRAY[]::text[], ARRAY['unit_name'], ARRAY['military_unit_name']),
    (46, ARRAY['equipment'], ARRAY['group_by','window_function','order_by','aggregate_function'], ARRAY['sum'], ARRAY['unit_id','last_replenishment','quantity'], ARRAY['month','total_ammo']),
    (48, ARRAY['soldier'], ARRAY['group_by','aggregate_function'], ARRAY['count'], ARRAY['status'], ARRAY[]::text[]),
    (73, ARRAY['soldier','military_service'], ARRAY['join','order_by'], ARRAY[]::text[], ARRAY['full_name','start_date','end_date'], ARRAY['days']),
    (50, ARRAY['enemy_unit','battle_enemy_unit','battle'], ARRAY['join'], ARRAY[]::text[], ARRAY['unit_name'], ARRAY[]::text[]),
    (51, ARRAY['battle'], ARRAY['group_by','order_by','aggregate_function'], ARRAY['extract','count'], ARRAY['start_date'], ARRAY['year','battles_count']),
    (52, ARRAY['soldier'], ARRAY[]::text[], ARRAY[]::text[], ARRAY['full_name','birth_year','enlistment_date'], ARRAY['enlistment_age']),
    (74, ARRAY['military_unit','military_service','soldier'], ARRAY['join','group_by','order_by','aggregate_function'], ARRAY['min','max'], ARRAY['unit_name','birth_year','enlistment_date'], ARRAY[]::text[]),
    (53, ARRAY['soldier'], ARRAY['group_by','order_by','aggregate_function'], ARRAY['avg','round'], ARRAY['enlistment_city','birth_year','enlistment_date'], ARRAY['avg_age']),

    -- Миссия 2: комплексная аналитика.
    (55, ARRAY['soldier','military_service','military_unit','soldier_medal'], ARRAY['join','group_by','window_function','order_by','aggregate_function'], ARRAY['count','dense_rank'], ARRAY['full_name','unit_name'], ARRAY['medals_count','medal_rank']),
    (78, ARRAY['battle','military_unit'], ARRAY['join','group_by','aggregate_function'], ARRAY['avg'], ARRAY['importance_level','combat_efficiency'], ARRAY['battle_group','avg_efficiency']),
    (57, ARRAY['military_unit','equipment'], ARRAY['join','window_function','order_by'], ARRAY['lag','lead'], ARRAY['unit_name','equipment_type','last_replenishment'], ARRAY['prev_replenishment','next_replenishment','days_between']),
    (58, ARRAY['military_unit','equipment'], ARRAY['join','subquery','group_by','order_by','aggregate_function'], ARRAY['avg','sum'], ARRAY['equipment_type','quantity'], ARRAY['total']),
    (81, ARRAY['military_unit','military_service','soldier','battle'], ARRAY['join','group_by','window_function','order_by','aggregate_function'], ARRAY['min','max','count','round','percent_rank'], ARRAY['unit_name','start_date','end_date','status'], ARRAY['total_duration','battles_count','losses','loss_per_battle_ratio','survival_percentile']),
    (80, ARRAY['military_unit','military_service','soldier','equipment','battle','soldier_medal'], ARRAY['join','group_by','order_by','aggregate_function'], ARRAY['count','group_concat'], ARRAY['unit_name','full_name','equipment_type'], ARRAY['soldiers_total','equipment_types','battles_participated','medals_received']),
    (59, ARRAY['equipment','military_unit'], ARRAY['window_function','order_by','aggregate_function'], ARRAY['avg','stddev'], ARRAY['item_name','quantity'], ARRAY[]::text[]),
    (60, ARRAY['enemy_unit','battle_enemy_unit','battle','military_unit','military_service','soldier'], ARRAY['cte','join','group_by','window_function','order_by','limit','aggregate_function'], ARRAY['rank','count'], ARRAY['unit_name'], ARRAY['victories','total_soviet_losses']),
    (82, ARRAY['equipment','equipment_assignment','military_service'], ARRAY['cte','join','group_by','window_function','order_by','aggregate_function'], ARRAY['avg','count'], ARRAY['equipment_type','issue_date','quantity'], ARRAY['year','loss_ratio','smoothed_ratio']),
    (61, ARRAY['military_unit','military_service','soldier','soldier_medal','medal','battle'], ARRAY['cte','join','group_by','order_by','aggregate_function'], ARRAY['count','round'], ARRAY['unit_name','medal_name','status'], ARRAY['awarded','deaths','victories','victory_per_medal','death_per_medal']),
    (83, ARRAY['battle'], ARRAY['group_by','order_by','aggregate_function'], ARRAY['extract','count'], ARRAY['end_date'], ARRAY['month_num','month_name','victory_count','victory_percentage']),
    (62, ARRAY['battle','military_unit','military_service','soldier','equipment','equipment_assignment'], ARRAY['cte','join','group_by','window_function','order_by','aggregate_function'], ARRAY['rank','count','avg','sum','round'], ARRAY['battle_name','status','combat_efficiency','quantity'], ARRAY['losses','avg_efficiency','equipment_used','loss_rank','eff_rank','cost_ratio'])
)
UPDATE public.tasks AS task
SET expected_result = task.expected_result || jsonb_build_object(
    'analysis_tables', to_jsonb(config.tables),
    'derive_requirements_from_tags', false,
    'analysis_requirements', jsonb_build_object(
        'required_tables', to_jsonb(config.tables),
        'required_features', to_jsonb(config.features),
        'required_functions', to_jsonb(config.functions),
        'required_selected_columns', to_jsonb(config.selected_columns),
        'required_output_aliases', to_jsonb(config.output_aliases)
    ),
    'analysis_context', jsonb_build_object('strict_schema', true),
    'quality_policy', jsonb_build_object(
        'max_penalty_rate', CASE task.mission_id
            WHEN 0 THEN 0.25
            WHEN 1 THEN 0.30
            ELSE 0.35
        END
    )
)
FROM task_config AS config
WHERE task.task_global_id = config.task_global_id
  AND task.mission_id IN (0, 1, 2)
  AND COALESCE(task.expected_result->>'mode', 'select') = 'select';

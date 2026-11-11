import json
from copy import deepcopy
from pathlib import Path
from typing import Dict, Any
from fastapi import HTTPException


class QuestLoader:
    _cache: Dict[str, dict] = {}
    _analysis_cache: Dict[str, dict] = {}
    _quests_dir = Path("content/quests")
    _analysis_dir = _quests_dir / "analysis"

    @classmethod
    def get_quest(cls, quest_id: str) -> dict:
        """Загружает квест из кэша или с диска"""
        if quest_id in cls._cache:
            return cls._cache[quest_id]

        file_path = cls._quests_dir / f"{quest_id}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Квест не найден")

        with open(file_path, "r", encoding="utf-8") as f:
            quest_data = json.load(f)
            cls._cache[quest_id] = quest_data
            return quest_data

    @classmethod
    def get_scene(cls, quest_id: str, scene_id: str) -> dict:
        """Получает конкретную сцену из квеста"""
        quest = cls.get_quest(quest_id)
        scene = quest.get("scenes", {}).get(scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Сцена не найдена")
        result = deepcopy(scene)
        analysis_config = cls._get_analysis_config(quest_id).get(scene_id, {})
        if analysis_config:
            expected_result = dict(result.get("expected_result") or {})
            expected_result.update(deepcopy(analysis_config))
            result["expected_result"] = expected_result
        return result

    @classmethod
    def _get_analysis_config(cls, quest_id: str) -> dict:
        """Загружает необязательные требования анализа для сцен квеста."""
        if quest_id in cls._analysis_cache:
            return cls._analysis_cache[quest_id]

        file_path = cls._analysis_dir / f"{quest_id}.json"
        if not file_path.exists():
            cls._analysis_cache[quest_id] = {}
            return {}

        with open(file_path, "r", encoding="utf-8") as file:
            config = json.load(file)
        if not isinstance(config, dict):
            raise ValueError("Конфигурация анализа квеста должна быть объектом")
        cls._analysis_cache[quest_id] = config
        return config
    
    @classmethod
    def get_all_quests(cls) -> list[dict]:
        """Возвращает информацию о всех доступных квестах"""
        quests = []
        if not cls._quests_dir.exists():
            return quests
        for file_path in cls._quests_dir.glob("*.json"):
            quest_id = file_path.stem
            try:
                quest_data = cls.get_quest(quest_id)
                quests.append({
                    "id": quest_id,
                    "title": quest_data.get("title", "Без названия"),
                    "description": quest_data.get("description", "Без описания")
                })
            except Exception:
                continue
        return quests

"""Форма заявки: проверка полей и нормализация телефона."""
import re

from django import forms

from .models import Lead

OBJECT_TYPES = [
    ("Отель", "Отель"),
    ("Мини-отель", "Мини-отель"),
    ("Апартаменты", "Апартаменты"),
    ("Сеть объектов", "Сеть объектов"),
    ("Другое", "Другое"),
]


class LeadForm(forms.ModelForm):
    # Скрытые служебные поля. website — ловушка для ботов, ts — время показа формы.
    website = forms.CharField(required=False)
    ts = forms.IntegerField(required=False)
    source_page = forms.CharField(required=False, max_length=255)

    object_type = forms.ChoiceField(choices=OBJECT_TYPES, label="Тип объекта")

    class Meta:
        model = Lead
        fields = ["name", "phone", "email", "object_type", "rooms_count", "message", "consent"]

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2:
            raise forms.ValidationError("Напишите имя.")
        return name

    def clean_phone(self):
        raw = self.cleaned_data["phone"]
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 11 and digits[0] in "78":
            digits = "7" + digits[1:]
        elif len(digits) == 10:
            digits = "7" + digits
        elif len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Проверьте номер телефона.")
        return "+" + digits

    def clean_consent(self):
        if not self.cleaned_data.get("consent"):
            raise forms.ValidationError("Нужно согласие на обработку персональных данных.")
        return True

    def clean_message(self):
        return self.cleaned_data.get("message", "").strip()[:4000]

    @property
    def is_bot(self):
        """Ловушка заполнена — форму отправил бот."""
        return bool(self.data.get("website"))


# --- Опросный лист для расчёта проекта ---------------------------------------
#
# Расширенная анкета. Дополнительные ответы не заводят новых полей в Lead:
# они складываются в текст заявки, чтобы модель, письмо и Telegram остались как есть.

CURRENT_SYSTEMS = [
    ("1С:Отель уже стоит", "1С:Отель уже стоит"),
    ("Другая учётная система или PMS", "Другая учётная система или PMS"),
    ("Онлайн-кассы", "Онлайн-кассы"),
    ("Электронные замки", "Электронные замки"),
    ("Модуль бронирования на сайте", "Модуль бронирования на сайте"),
    ("Учёт ведётся вручную", "Учёт ведётся вручную"),
]

PROJECT_TASKS = [
    ("Внедрение 1С:Отель", "Внедрение 1С:Отель"),
    ("Онлайн-кассы и эквайринг", "Онлайн-кассы и эквайринг"),
    ("Серверы и сеть", "Серверы и сеть"),
    ("Электронные замки", "Электронные замки"),
    ("Каналы продаж и бронирование", "Каналы продаж и бронирование"),
    ("Перенос данных из старой системы", "Перенос данных из старой системы"),
    ("Обучение персонала", "Обучение персонала"),
    ("Поддержка 24/7", "Поддержка 24/7"),
]

TIMELINES = [
    ("Как можно скорее", "Как можно скорее"),
    ("В ближайшие 1–3 месяца", "В ближайшие 1–3 месяца"),
    ("К следующему сезону", "К следующему сезону"),
    ("Пока оцениваем", "Пока оцениваем"),
]


class EstimateForm(LeadForm):
    object_name = forms.CharField(label="Название объекта", required=False, max_length=150)
    workplaces = forms.IntegerField(label="Рабочих мест", required=False, min_value=1, max_value=999)
    systems = forms.MultipleChoiceField(label="Что уже есть", choices=CURRENT_SYSTEMS, required=False)
    tasks = forms.MultipleChoiceField(label="Что нужно сделать", choices=PROJECT_TASKS, required=False)
    timeline = forms.ChoiceField(label="Сроки", choices=TIMELINES, required=False)

    def clean(self):
        cleaned = super().clean()
        answers = [
            ("Объект", cleaned.get("object_name")),
            ("Рабочих мест", cleaned.get("workplaces")),
            ("Уже есть", ", ".join(cleaned.get("systems") or [])),
            ("Нужно", ", ".join(cleaned.get("tasks") or [])),
            ("Сроки", cleaned.get("timeline")),
        ]
        lines = [f"{label}: {value}" for label, value in answers if value]
        if cleaned.get("message"):
            lines.append("Комментарий: " + cleaned["message"])
        cleaned["message"] = "\n".join(["Опросный лист", *lines])[:4000]
        return cleaned

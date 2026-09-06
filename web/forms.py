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

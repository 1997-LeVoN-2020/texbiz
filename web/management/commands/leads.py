"""
Читает заявки прямо на сервере, без админки.

    manage.py leads                 последние 20
    manage.py leads --days 7        за неделю
    manage.py leads --status new    только новые
    manage.py leads --all           все
    manage.py leads --csv leads.csv выгрузить в файл
    manage.py leads --count         только количество

Зачем: пока админка не подключена, заявка видна только в письме. Если почта
отвалится — а на прежней версии сайта обработчик формы вовсе не был
развёрнут, и обращения пропадали, — это единственный способ увидеть, что
людям отвечать. Команда только читает, ничего не меняет.
"""
import csv
import sys
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from web.models import Lead

STATUS_WIDTH = max(len(label) for _, label in Lead.Status.choices)


class Command(BaseCommand):
    help = "Показывает заявки с сайта. Только чтение."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="все заявки, а не последние 20")
        parser.add_argument("--days", type=int, help="только за последние N дней")
        parser.add_argument(
            "--status",
            choices=[value for value, _ in Lead.Status.choices],
            help="только с этим статусом",
        )
        parser.add_argument("--csv", metavar="ФАЙЛ", help="выгрузить в CSV вместо вывода на экран")
        parser.add_argument("--count", action="store_true", help="показать только количество")

    def handle(self, *args, **options):
        leads = Lead.objects.all()

        if options["status"]:
            leads = leads.filter(status=options["status"])
        if options["days"]:
            leads = leads.filter(created_at__gte=timezone.now() - timedelta(days=options["days"]))

        total = leads.count()

        if options["count"]:
            self.stdout.write(str(total))
            return

        if not options["all"] and not options["csv"]:
            leads = leads[:20]

        if options["csv"]:
            self.export(leads, options["csv"], total)
            return

        if total == 0:
            self.stdout.write("Заявок нет.")
            return

        self.show(leads, total, options["all"])

    def show(self, leads, total, show_all):
        shown = 0
        for lead in leads:
            shown += 1
            head = (
                f"#{lead.pk}  {lead.created_at:%d.%m.%Y %H:%M}  "
                f"[{lead.get_status_display():<{STATUS_WIDTH}}]  {lead.name}"
            )
            self.stdout.write(self.style.MIGRATE_HEADING(head))
            self.stdout.write(f"    {lead.phone}" + (f" · {lead.email}" if lead.email else ""))

            details = [lead.object_type]
            if lead.rooms_count:
                details.append(f"{lead.rooms_count} номеров")
            if lead.source_page:
                details.append(f"со страницы {lead.source_page}")
            self.stdout.write("    " + " · ".join(details))

            if lead.message:
                for line in self.wrap(lead.message, 76):
                    self.stdout.write(f"    {line}")
            self.stdout.write("")

        if not show_all and total > shown:
            self.stdout.write(
                f"Показано {shown} из {total}. Все — с ключом --all, выгрузка — с --csv файл.csv"
            )
        else:
            self.stdout.write(f"Всего: {total}")

    def export(self, leads, path, total):
        columns = [
            ("Дата", lambda x: f"{x.created_at:%d.%m.%Y %H:%M}"),
            ("Имя", lambda x: x.name),
            ("Телефон", lambda x: x.phone),
            ("E-mail", lambda x: x.email),
            ("Тип объекта", lambda x: x.object_type),
            ("Номерной фонд", lambda x: x.rooms_count or ""),
            ("Задача", lambda x: x.message),
            ("Страница", lambda x: x.source_page),
            ("Статус", lambda x: x.get_status_display()),
        ]
        # utf-8-sig: без метки Excel открывает кириллицу как набор символов.
        with open(path, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle, delimiter=";")
            writer.writerow([name for name, _ in columns])
            for lead in leads:
                writer.writerow([get(lead) for _, get in columns])
        self.stdout.write(f"Выгружено заявок: {total} → {path}")

    @staticmethod
    def wrap(text, width):
        words, line, lines = text.split(), "", []
        for word in words:
            if len(line) + len(word) + 1 > width:
                lines.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            lines.append(line)
        return lines

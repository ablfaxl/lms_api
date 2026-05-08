from math import ceil
from pathlib import Path

from django.apps import apps
from django.core.management import BaseCommand
from PIL import Image, ImageDraw, ImageFont


class Command(BaseCommand):
    help = "Generate DB schema diagram image directly from Django models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="docs/images/db_schema.png",
            help="Output image path (default: docs/images/db_schema.png)",
        )

    def handle(self, *args, **options):
        output = Path(options["output"])
        output.parent.mkdir(parents=True, exist_ok=True)

        model_specs = []
        for app_label in ("accounts", "courses"):
            app_config = apps.get_app_config(app_label)
            for model in app_config.get_models():
                fields = []
                relations = []
                for field in model._meta.get_fields():
                    if field.auto_created and not field.concrete:
                        continue
                    if field.is_relation:
                        rel_model = getattr(field, "related_model", None)
                        if rel_model is not None:
                            relations.append((field.name, rel_model.__name__))
                            if field.concrete:
                                fields.append(f"{field.name}: {field.__class__.__name__}")
                    elif field.concrete:
                        fields.append(f"{field.name}: {field.get_internal_type()}")
                model_specs.append(
                    {
                        "name": model.__name__,
                        "app": app_label,
                        "fields": fields,
                        "relations": relations,
                    }
                )

        if not model_specs:
            self.stdout.write(self.style.WARNING("No models found."))
            return

        font = ImageFont.load_default()
        title_h = 20
        line_h = 14
        box_w = 360
        box_gap_x = 48
        box_gap_y = 28
        max_field_lines = max(max(len(m["fields"]), 1) for m in model_specs)
        box_h = title_h + (max_field_lines + 2) * line_h
        cols = 3
        rows = ceil(len(model_specs) / cols)
        width = 48 + cols * box_w + (cols - 1) * box_gap_x + 48
        height = 48 + rows * box_h + (rows - 1) * box_gap_y + 48

        image = Image.new("RGB", (width, height), (250, 252, 255))
        draw = ImageDraw.Draw(image)

        positions = {}
        for idx, spec in enumerate(model_specs):
            row, col = divmod(idx, cols)
            x = 48 + col * (box_w + box_gap_x)
            y = 48 + row * (box_h + box_gap_y)
            x2 = x + box_w
            y2 = y + box_h
            positions[spec["name"]] = (x, y, x2, y2)

            fill = (236, 244, 255) if spec["app"] == "courses" else (239, 255, 244)
            draw.rounded_rectangle((x, y, x2, y2), radius=10, fill=fill, outline=(80, 98, 130), width=2)
            draw.text((x + 10, y + 6), f"{spec['name']}  ({spec['app']})", font=font, fill=(25, 40, 60))
            draw.line((x + 8, y + title_h, x2 - 8, y + title_h), fill=(130, 146, 170), width=1)

            for i, field_line in enumerate(spec["fields"][: max_field_lines + 1]):
                draw.text((x + 10, y + title_h + 6 + i * line_h), field_line, font=font, fill=(36, 50, 72))

        for spec in model_specs:
            sx1, sy1, sx2, sy2 = positions[spec["name"]]
            start = (sx2, (sy1 + sy2) // 2)
            for field_name, target_name in spec["relations"]:
                target = positions.get(target_name)
                if not target:
                    continue
                tx1, ty1, tx2, ty2 = target
                end = (tx1, (ty1 + ty2) // 2)
                color = (90, 95, 110)
                draw.line((start[0], start[1], end[0], end[1]), fill=color, width=2)
                mx = (start[0] + end[0]) // 2 + 2
                my = (start[1] + end[1]) // 2 - 10
                draw.text((mx, my), field_name, font=font, fill=(70, 70, 80))

        image.save(output.as_posix(), format="PNG")
        self.stdout.write(self.style.SUCCESS(f"Schema diagram generated: {output.as_posix()}"))

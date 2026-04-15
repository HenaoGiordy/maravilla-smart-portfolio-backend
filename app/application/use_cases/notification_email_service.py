from typing import Protocol

from app.config.settings import Settings
from app.domain.entities.notification import NotificationEvent


class EmailSender(Protocol):
    def send_email(self, recipient_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        ...


class NotificationEmailService:
    def __init__(self, settings: Settings, email_sender: EmailSender) -> None:
        self._settings = settings
        self._email_sender = email_sender

    def _build_subject(self, event: NotificationEvent) -> str:
        prefix = self._settings.notifications_email_subject_prefix.strip()
        if event.event_type == "user_registered":
            return f"{prefix} Bienvenida a Maravilla"
        if event.event_type == "profile_assigned":
            return f"{prefix} Perfil de inversión asignado"
        if event.event_type == "variable_income_update":
            return f"{prefix} Informe ejecutivo de inversiones"
        return f"{prefix} Notificación de cuenta"

    def _build_text_body(self, event: NotificationEvent) -> str:
        if event.event_type == "user_registered":
            name = event.metadata.get("name", "inversionista")
            return (
                f"Hola {name},\n\n"
                "Tu cuenta en Maravilla fue creada correctamente.\n"
                "Ahora puedes completar tu onboarding y definir tu perfil de inversión.\n\n"
                "Equipo Maravilla"
            )

        if event.event_type == "profile_assigned":
            profile_name = event.metadata.get("profile_name", "No definido")
            risk_level = event.metadata.get("risk_level", "No definido")
            return (
                "Tu perfil de inversión ya fue asignado.\n\n"
                f"Perfil: {profile_name}\n"
                f"Riesgo: {risk_level}\n\n"
                "Ya puedes continuar con la gestión de tu portafolio en Maravilla.\n\n"
                "Equipo Maravilla"
            )

        if event.event_type == "variable_income_update":
            assets = event.metadata.get("assets", [])
            lines = [
                "Informe ejecutivo de inversiones",
                "",
                "En Maravilla nos preocupamos por la salud de tu portafolio y estamos aquí para asesorarte en tus decisiones financieras.",
                "A continuación, te compartimos un resumen de la evolución reciente en renta variable:",
                "",
            ]
            for asset in assets:
                lines.append(
                    f"- {asset.get('name', 'Activo')}: {asset.get('allocation_percentage', 0)}% · +{asset.get('annual_return_percentage', 0)}% E.A."
                )
            lines.append("")
            lines.append("Recomendación ejecutiva:")
            lines.append("Evalúa tu exposición actual, balancea riesgo-retorno y mantén la estrategia alineada con tu perfil de inversión.")
            lines.append("")
            lines.append("Si deseas, nuestro equipo puede acompañarte con una revisión personalizada de tu portafolio.")
            lines.append("")
            lines.append("Equipo de Asesoría Maravilla")
            return "\n".join(lines)

        return (
            "Recibimos una actualización sobre tu cuenta en Maravilla.\n"
            f"Evento: {event.event_type}\n\n"
            "Equipo Maravilla"
        )

    def _build_html_body(self, event: NotificationEvent) -> str | None:
        if event.event_type != "variable_income_update":
            return None

        assets = event.metadata.get("assets", [])
        rows = "".join(
            [
                (
                    "<tr>"
                    f"<td style='padding:10px 12px;border-bottom:1px solid #3f3f46;color:#f4f4f5'>{asset.get('name', 'Activo')}</td>"
                    f"<td style='padding:10px 12px;border-bottom:1px solid #3f3f46;color:#facc15;text-align:center'>{asset.get('allocation_percentage', 0)}%</td>"
                    f"<td style='padding:10px 12px;border-bottom:1px solid #3f3f46;color:#facc15;text-align:right'>+{asset.get('annual_return_percentage', 0)}% E.A.</td>"
                    "</tr>"
                )
                for asset in assets
            ]
        )

        return (
            "<div style='font-family:Inter,Arial,sans-serif;background:#18181b;padding:24px;color:#f4f4f5'>"
            "<div style='max-width:720px;margin:0 auto;background:#27272a;border:1px solid #3f3f46;border-radius:12px;overflow:hidden'>"
            "<div style='padding:18px 20px;background:#3f3f46'>"
            "<h2 style='margin:0;color:#facc15;font-size:18px'>Informe Ejecutivo de Inversiones</h2>"
            "<p style='margin:8px 0 0;color:#d4d4d8;font-size:13px'>Renta Variable · Acciones y ETFs</p>"
            "</div>"
            "<div style='padding:20px'>"
            "<p style='margin:0 0 10px;color:#e4e4e7;line-height:1.6'>En Maravilla nos preocupamos por tus inversiones y estamos aquí para asesorarte en cada etapa de tu estrategia financiera.</p>"
            "<p style='margin:0 0 16px;color:#d4d4d8;line-height:1.6'>Este resumen presenta una visión ejecutiva de los movimientos recientes para facilitar una toma de decisiones informada.</p>"
            "<table style='width:100%;border-collapse:collapse;background:#18181b;border-radius:8px'>"
            "<thead><tr>"
            "<th style='text-align:left;padding:10px 12px;color:#a1a1aa;border-bottom:1px solid #3f3f46'>Activo</th>"
            "<th style='text-align:center;padding:10px 12px;color:#a1a1aa;border-bottom:1px solid #3f3f46'>Peso</th>"
            "<th style='text-align:right;padding:10px 12px;color:#a1a1aa;border-bottom:1px solid #3f3f46'>Retorno</th>"
            "</tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
            "<div style='margin-top:16px;padding:14px;border:1px solid #3f3f46;border-radius:8px;background:#18181b'>"
            "<p style='margin:0 0 8px;color:#f4f4f5;font-weight:600'>Recomendación ejecutiva</p>"
            "<p style='margin:0;color:#d4d4d8;line-height:1.6'>Revisa la concentración por activo, valida la relación riesgo-retorno y ajusta la asignación para mantener consistencia con tu perfil de inversión.</p>"
            "</div>"
            "<p style='margin:16px 0 0;color:#d4d4d8;line-height:1.6'>Si lo deseas, podemos acompañarte con una asesoría personalizada para tu próxima decisión de inversión.</p>"
            "<p style='margin:8px 0 0;color:#f4f4f5'>Equipo de Asesoría Maravilla</p>"
            "</div>"
            "</div>"
            "</div>"
        )

    def send_event_email(self, event: NotificationEvent) -> None:
        subject = self._build_subject(event)
        text_body = self._build_text_body(event)
        html_body = self._build_html_body(event)
        self._email_sender.send_email(
            recipient_email=event.email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

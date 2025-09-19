from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver(post_save, sender="core.Shift")
@receiver(post_delete, sender="core.Shift")
def update_service_hours(sender, instance, **kwargs):
    """
    Update total_hours and total_hours_planned for the related Service
    when a Shift is saved or deleted.
    """
    if instance.service:
        # Import here to avoid circular imports
        from core.models import Service, Shift

        service = instance.service

        # Calculate total hours worked (from completed shifts)
        total_hours = (
            service.shifts.filter(status=Shift.Status.COMPLETED).aggregate(
                total=models.Sum("hours_worked")
            )["total"]
            or 0
        )

        # Calculate total planned hours (from all shifts)
        # Check if planned_hours_worked field exists (might not exist yet during migration)
        try:
            total_hours_planned = (
                service.shifts.all().aggregate(
                    total=models.Sum("planned_hours_worked")
                )["total"]
                or 0
            )
            # Convert Decimal to int for planned hours (round to nearest int)
            if hasattr(total_hours_planned, "quantize"):
                total_hours_planned = int(round(float(total_hours_planned)))

        except Exception:
            # Field doesn't exist yet, set to 0
            total_hours_planned = 0

        # Update the service fields
        Service.objects.filter(id=service.id).update(
            total_hours=total_hours, total_hours_planned=total_hours_planned
        )


@receiver(post_save, sender="core.Service")
def initialize_service_hours(sender, instance, created, **kwargs):
    """
    Initialize total_hours and total_hours_planned when a new Service is created.
    """
    if created:
        # For new services, initialize both fields to 0
        # Use update to avoid triggering another signal
        sender.objects.filter(id=instance.id).update(
            total_hours=0, total_hours_planned=0
        )

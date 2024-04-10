from time import sleep

from django.core.mail import send_mail
from django import forms


class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Email")
    message = forms.CharField(
        label="Сообщение", widget=forms.Textarea(attrs={"rows": 5})
    )

    def send_email(self):
        """Sends an email when the feedback form has been submitted."""
        sleep(20)  # Simulate expensive operation(s) that freeze Django
        send_mail(
            "Твой отзыв",
            f"\t{self.cleaned_data['message']}\n\nСпасибо!",
            "support@example.com",
            [self.cleaned_data["email"]],
            fail_silently=False,
        )

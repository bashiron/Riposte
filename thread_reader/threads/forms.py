from django import forms

class LinkForm(forms.Form):
    tw_link = forms.URLField(label='Link del Tweet')

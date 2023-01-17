#-*- coding: utf-8 -*-
from django import forms

class answer(forms.Form):
    ans_opt_sol = forms.CharField(max_length = 200,required=False)
    ans_opt_val = forms.CharField(max_length = 200,required=False)
    ans_certificato = forms.CharField(max_length = 200,required=False)
    ans_certificato2 = forms.CharField(max_length = 200,required=False)

class uploaded_file(forms.Form):
    file = forms.FileField()

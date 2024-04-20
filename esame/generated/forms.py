#-*- coding: utf-8 -*-
from django import forms

class answer(forms.Form):
    ans_opt_sol = forms.CharField(max_length = 200,required=False)
    ans_opt_val = forms.CharField(max_length = 200,required=False)
    ans_num_opt_sols = forms.CharField(max_length = 200,required=False)
    ans_edge_classification = forms.CharField(max_length = 200,required=False)

class uploaded_file(forms.Form):
    file = forms.FileField()

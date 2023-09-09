#-*- coding: utf-8 -*-
from django import forms

class answer(forms.Form):
    ans_opt_sol = forms.CharField(max_length = 200,required=False)
    ans_opt_val = forms.CharField(max_length = 200,required=False)
    ans_num_opt_sols = forms.CharField(max_length = 200,required=False)
    ans_n = forms.CharField(max_length = 200,required=False)
    ans_o = forms.CharField(max_length = 200,required=False)
    ans_t = forms.CharField(max_length = 200,required=False)
    ans_  = forms.CharField(max_length = 200,required=False)
    ans_a = forms.CharField(max_length = 200,required=False)
    ans_T = forms.CharField(max_length = 200,required=False)
    ans_A = forms.CharField(max_length = 200,required=False)
    ans_L = forms.CharField(max_length = 200,required=False)
    ans_i = forms.CharField(max_length = 200,required=False)
    ans_g = forms.CharField(max_length = 200,required=False)
    ans_h = forms.CharField(max_length = 200,required=False)
    ans_v = forms.CharField(max_length = 200,required=False)
    ans_e = forms.CharField(max_length = 200,required=False)
    ans_r = forms.CharField(max_length = 200,required=False)
    ans_f = forms.CharField(max_length = 200,required=False)
    ans_y = forms.CharField(max_length = 200,required=False)
    ans_s = forms.CharField(max_length = 200,required=False)
    ans_c = forms.CharField(max_length = 200,required=False)
    ans_l = forms.CharField(max_length = 200,required=False)
    ans_edge_classification = forms.CharField(max_length = 200,required=False)

class uploaded_file(forms.Form):
    file = forms.FileField()

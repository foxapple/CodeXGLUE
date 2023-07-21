import datetime

from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
import stripe

from monospace.forms import *
from monospace.models import *
import monospace.settings as settings

stripe.api_key = settings.STRIPE_SECRET

def soon():
  soon = datetime.date.today() + datetime.timedelta(days=30)
  return {'month': soon.month, 'year': soon.year}

def home(request):
  uid = request.session.get('user')
  if uid is None:
    return render_to_response('home.html')
  else:
    return render_to_response('user.html', {'user': User.objects.get(pk=uid)})

def sign_in(request):
  user = None
  if request.method == 'POST':
    form = SignInForm(request.POST)
    if form.is_valid():
      results = User.objects.filter(email=form.cleaned_data['email'])
      if len(results) == 1:
        if results[0].check_password(form.cleaned_data['password']):
          request.session['user'] = results[0].pk
          return HttpResponseRedirect('/')
        else:
          form.addError('Incorrect email address or password')
      else:
        form.addError('Incorrect email address or password')
  else:
    form = SignInForm()
    
  print form.non_field_errors()

  return render_to_response(
    'sign_in.html',
    {
      'form': form,
      'user': user
    },
    context_instance=RequestContext(request)
  )

def sign_out(request):
  del request.session['user']
  return HttpResponseRedirect('/')

def register(request):
  user = None
  if request.method == 'POST':
    form = UserForm(request.POST)
    if form.is_valid():

      customer = stripe.Customer.create(
        description = form.cleaned_data['email'],
        card = form.cleaned_data['stripe_token'],
        plan = 'basic'
      )

      user = User(
        name = form.cleaned_data['name'],
        email = form.cleaned_data['email'],
        last_4_digits = form.cleaned_data['last_4_digits'],
        stripe_id = customer.id
      )
      user.set_password(form.cleaned_data['password1'])

      try:
        user.save()
      except IntegrityError:
        form.addError(user.email + ' is already a member')
      else:
        request.session['user'] = user.pk
        return HttpResponseRedirect('/')

  else:
    form = UserForm()

  return render_to_response(
    'register.html',
    {
      'form': form,
      'months': range(1, 13),
      'publishable': settings.STRIPE_PUBLISHABLE,
      'soon': soon(),
      'user': user,
      'years': range(2011, 2036),
    },
    context_instance=RequestContext(request)
  )

def edit(request):
  uid = request.session.get('user')
  if uid is None:
    return HttpResponseRedirect('/')
  user = User.objects.get(pk=uid)
  if request.method == 'POST':
    form = CardForm(request.POST)
    if form.is_valid():

      customer = stripe.Customer.retrieve(user.stripe_id)
      customer.card = form.cleaned_data['stripe_token']
      customer.save()

      user.last_4_digits = form.cleaned_data['last_4_digits']
      user.stripe_id = customer.id
      user.save()

      return HttpResponseRedirect('/')

  else:
    form = CardForm()

  return render_to_response(
    'edit.html',
    {
      'form': form,
      'publishable': settings.STRIPE_PUBLISHABLE,
      'soon': soon(),
      'months': range(1, 13),
      'years': range(2011, 2036)
    },
    context_instance=RequestContext(request)
  )



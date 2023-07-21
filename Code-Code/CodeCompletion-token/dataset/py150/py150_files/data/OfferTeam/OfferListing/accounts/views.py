from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import authenticate, login
from django.shortcuts import render, get_object_or_404
from accounts.forms import UserEditForm, UserConfirmDeletionForm, UserRegisterForm
from django.contrib import messages
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth import logout as logout_user
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from offers.models import Comment, Offer
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import User


@login_required
def self_profile(request):
    return render(request, 'accounts/self_profile.html', {"user": request.user})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    comments = user.comment_set.filter(status=Comment.PUBLISHED, offer__status=Offer.PUBLISHED).order_by('-created_at')

    paginator = Paginator(comments, 5)

    page = request.GET.get('page')
    try:
        comments = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        comments = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        comments = paginator.page(paginator.num_pages)

    return render(request, 'accounts/profile.html', {
        "user": user,
        "comments": comments,
    })


@login_required
def edit_account(request):
    if request.method == "POST":
        form = UserEditForm(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data["first_name"]
            request.user.last_name = form.cleaned_data["last_name"]
            request.user.email = form.cleaned_data["email"]
            request.user.save()
            messages.success(request, 'You account has been successfully updated!')
        else:
            messages.error(request, 'The form had errors. Please correct them and submit again.')
    else:
        form = UserEditForm({
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
        })
    return render(request, 'accounts/edit.html', {"form": form})


@login_required
def change_password(request):
    helper = FormHelper()
    helper.add_input(Submit('save', 'Change Password'))

    if request.method == "POST":
        form = PasswordChangeForm(
            request.user,
            request.POST
        )
        if form.is_valid():
            messages.success(request, "You password has been changed!")
            form.save()
    else:
        form = PasswordChangeForm(request.user)

    form.helper = helper
    return render(request, 'accounts/change_password.html', {"form": form})


@login_required
def deactivate_account(request):
    if request.method == "POST":
        form = UserConfirmDeletionForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
            if user is None or user != request.user:
                messages.error(request, "Invalid username or password!")
            else:
                request.user.is_active = False
                request.user.save()
                logout_user(request)
                messages.success(
                    request,
                    "Your account has been deactivated! Please contact a staff member to reactivate your account!"
                )
                return HttpResponseRedirect(reverse("home"))
    else:
        form = UserConfirmDeletionForm()
    return render(request, 'accounts/deactivate.html', {"form": form})


@login_required
def comment_list(request):
    comments_list = Comment.visible.filter(commenter=request.user).order_by('-created_at')

    paginator = Paginator(comments_list, 10)
    page = request.GET.get('page')
    try:
        comments = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        comments = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        comments = paginator.page(paginator.num_pages)

    return render(request, 'accounts/comments.html', {"comments": comments})


@login_required
def followed_list(request):
    offer_list = Offer.visible_offers.filter(followers=request.user)

    paginator = Paginator(offer_list, 5)
    page = request.GET.get('page')
    try:
        offers = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        offers = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        offers = paginator.page(paginator.num_pages)

    return render(request, 'accounts/offers.html', {"offers": offers})


def register(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('home'))
    if request.method == "POST":
        user = User(is_staff=False, is_superuser=False)
        form = UserRegisterForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password1"])
            login(request, user)
            messages.success(request, "Thank you for registering!")
            return HttpResponseRedirect(reverse('home'))
        else:
            messages.error(request, "You had errors in your details. Please fix them and submit again.")
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {"form": form})

from django.views.generic import TemplateView, ListView, DeleteView, CreateView, UpdateView, DetailView
from dictionary.models import Term, Flag
from users.models import Profile
from dictionary.forms import TermForm
from random import choice
from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseNotFound
from random import choice
from allauth.account.forms import LoginForm
import json
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, SearchHeadline

twitter_icon = '''
<svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      fill="currentColor"
      class="bi bi-twitter"
      viewBox="0 0 16 16"
    >
      <path
        d="M5.026 15c6.038 0 9.341-5.003 9.341-9.334 0-.14 0-.282-.006-.422A6.685 6.685 0 0 0 16 3.542a6.658 6.658 0 0 1-1.889.518 3.301 3.301 0 0 0 1.447-1.817 6.533 6.533 0 0 1-2.087.793A3.286 3.286 0 0 0 7.875 6.03a9.325 9.325 0 0 1-6.767-3.429 3.289 3.289 0 0 0 1.018 4.382A3.323 3.323 0 0 1 .64 6.575v.045a3.288 3.288 0 0 0 2.632 3.218 3.203 3.203 0 0 1-.865.115 3.23 3.23 0 0 1-.614-.057 3.283 3.283 0 0 0 3.067 2.277A6.588 6.588 0 0 1 .78 13.58a6.32 6.32 0 0 1-.78-.045A9.344 9.344 0 0 0 5.026 15z"
      />
</svg>
'''

facebook_icon = '''
<svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      fill="currentColor"
      class="bi bi-facebook p-0"
      viewBox="0 0 16 16"
    >
      <path
        d="M16 8.049c0-4.446-3.582-8.05-8-8.05C3.58 0-.002 3.603-.002 8.05c0 4.017 2.926 7.347 6.75 7.951v-5.625h-2.03V8.05H6.75V6.275c0-2.017 1.195-3.131 3.022-3.131.876 0 1.791.157 1.791.157v1.98h-1.009c-.993 0-1.303.621-1.303 1.258v1.51h2.218l-.354 2.326H9.25V16c3.824-.604 6.75-3.934 6.75-7.951z"
      />
</svg>
'''

whatsapp_icon = '''
<svg
      xmlns="http://www.w3.org/2000/svg"
      width="16"
      height="16"
      fill="currentColor"
      class="bi bi-whatsapp"
      viewBox="0 0 16 16"
    >
      <path
        d="M13.601 2.326A7.854 7.854 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.933 7.933 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.898 7.898 0 0 0 13.6 2.326zM7.994 14.521a6.573 6.573 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.557 6.557 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592zm3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.729.729 0 0 0-.529.247c-.182.198-.691.677-.691 1.654 0 .977.71 1.916.81 2.049.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232z"
      />
</svg>
'''

icons = {
    'twitter': twitter_icon,
    'facebook': facebook_icon,
    'whatsapp': whatsapp_icon
}


class IndexView(ListView):
    """Handle functionality for the homepage"""
    template_name = 'dictionary/index.html'
    context_object_name = 'terms'
    paginate_by = 10

    def get_queryset(self):
        # count votes and add them to terms context--
        queryset = Term.objects.filter(approved=True).annotate(
            upvotes_count=Count('upvote', distinct=True),
            downvotes_count=Count(
                'downvote', distinct=True)
        ).order_by('-date')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        form = LoginForm()
        try:
            qs_json = json.dumps(list(Term.objects.filter(
                approved=True).values()), indent=4, sort_keys=True, default=str)
        except:
            qs_json = []

        context.update({
            # 'terms': terms,
            'form': form,
            'user': self.request.user,
            'qs_json': qs_json,
            'icons': icons
        })

        return context

    def post(self, request, *args, **kwargs):
        # check if user is authenticated
        if request.user.is_authenticated:
            term_id = request.POST.get('term_id')

            # is_ajax() method deprecated in this version of django hence wrote my own
            def is_ajax(request):
                return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

            if is_ajax(request=request):
                term_id = request.POST.get('term_id')
                term = get_object_or_404(Term, pk=int(term_id))
                auth_profile = Profile.objects.get(user=term.author)

                # get profile
                profile = Profile.objects.get(user=request.user)
                if request.POST.get('form') == "vote":
                    term_id = request.POST.get('term_id')
                    term = get_object_or_404(Term, pk=int(term_id))
                    vote_type = request.POST.get('button')

                    userUpVotes = term.upvote.filter(
                        id=request.user.id).count()
                    userDownVotes = term.downvote.filter(
                        id=request.user.id).count()

                    if vote_type == "upVote":
                        if userUpVotes == 0 and userDownVotes == 0:
                            term.upvote.add(request.user)
                            # profile.reputation += 2
                            auth_profile.reputation += 2
                            profile.save()
                        elif userUpVotes == 1:
                            term.upvote.remove(request.user)
                            # profile.reputation -= 2
                            auth_profile.reputation -= 2
                            profile.save()
                        elif userDownVotes == 1 and userUpVotes == 0:
                            term.downvote.remove(request.user)
                            term.upvote.add(request.user)

                    elif vote_type == "downVote":
                        if userDownVotes == 0 and userUpVotes == 0:
                            term.downvote.add(request.user)
                            # profile.reputation += 2
                            auth_profile.reputation += 2
                            profile.save()
                        elif userDownVotes == 1:
                            term.downvote.remove(request.user)
                            # profile.reputation -= 2
                            auth_profile.reputation -= 2
                            profile.save()
                        elif userUpVotes == 1 and userDownVotes == 0:
                            term.upvote.remove(request.user)
                            term.downvote.add(request.user)
                elif request.POST.get('form') == "flag":
                    term_id = request.POST.get('term_id')
                    reason = request.POST.get('reason')
                    other_reason = request.POST.get('other_reason')
                    user = request.user
                    term = get_object_or_404(Term, pk=int(term_id))
                    flags = term.flag_set.all()

                    # check if flags exist
                    if flags:
                        # check if user has flags
                        flag = term.flag_set.filter(flagged_by=user)
                        if flag:
                            flag.update(reason=reason,
                                        other_reason=other_reason)
                        else:
                            flag = Flag(word=term, reason=reason,
                                        other_reason=other_reason, flagged_by=user)
                            flag.save()
                            profile.reputation += 5
                            auth_profile.reputation -= 1
                            profile.save()
                    else:
                        flag = Flag(word=term, reason=reason,
                                    other_reason=other_reason, flagged_by=user)
                        flag.save()
                        profile.reputation += 5
                        auth_profile.reputation -= 1
                        profile.save()
            else:
                pass

            # count number of votes to be shown to user after successfull post
            num_upvotes = Term.objects.all().annotate(
                upvotes_count=Count('upvote')
            )
            num_downvotes = Term.objects.all().annotate(
                downvotes_count=Count('downvote')
            )

            # get index of term in results for json
            def search(term_id):
                try:
                    term = get_object_or_404(Term, pk=int(term_id))
                    up = list(num_upvotes).index(term)
                    down = list(num_downvotes).index(term)
                    index = {
                        'upvote': up,
                        'downvote': down
                    }
                    return index
                except ValueError:
                    return 'not found'

            index = search(term_id)
            # convert data to json to be sent to jquery(client)
            data = json.dumps({
                'num_upvotes': num_upvotes[index['upvote']].upvotes_count,
                'num_downvotes': num_downvotes[index['downvote']].downvotes_count,
                'message': "Report submitted successfully"
            })

            return JsonResponse({"data": data}, status=200)
        else:
            pass

    def get(self, request, *args, **kwargs):
        # is_ajax() method deprecated in this version of django hence wrote my own
        def is_ajax(request):
            return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        # check if cookies are working on browser
        request.session.set_test_cookie()

        # Check that the test cookie worked
        if request.session.test_cookie_worked():
            # delete the test cookie
            request.session.delete_test_cookie()

            request.session['has_voted'] = False
            # cookie for new word submission
            request.session['submit'] = False

            if is_ajax(request=request):

                term_id = request.GET.get('term_id')
                button = request.GET.get('button')

                request.session['term_id'] = term_id
                request.session['button'] = button
                request.session['has_voted'] = True

            else:
                pass
        else:
            return HttpResponse("Our site uses cookies. Please enable cookies and try again.")

        return super().get(request, *args, **kwargs)


class SearchView(IndexView):
    template_name = 'dictionary/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get('q')
        vector = SearchVector('word', weight='A') + SearchVector('definition',
                                                                 weight='B') + SearchVector('other_definitions', weight='C')
        query = SearchQuery(q, search_type='plain')
        results = Term.objects.annotate(search=vector, rank=SearchRank(
            vector, query)).filter(search=q, approved=True).order_by('-rank')
        # results = Term.objects.annotate(
        #     headline=SearchHeadline(
        #     vector,
        #     query,
        #     start_sel='<b>',
        #     stop_sel='</b>',
        #     ),
        #     ).get()
        context.update({
            'results': results,
            'q': q
        })
        return context


class RandomView(TemplateView):
    template_name = 'dictionary/random.html'

    def get_context_data(self, **kwargs):
        context = super(RandomView, self).get_context_data(**kwargs)
        form = LoginForm
        pks = Term.objects.filter(approved=True).values_list('pk', flat=True)
        random_pk = choice(pks)
        random_term = Term.objects.filter(pk=random_pk).annotate(
            upvotes_count=Count('upvote', distinct=True),
            downvotes_count=Count(
                'downvote', distinct=True,)
        )
        term = random_term[0]
        qs_json = json.dumps(list(Term.objects.filter(approved=True).values()),
                             indent=4, sort_keys=True, default=str)

        context.update({
            'object': term,
            'form': form,
            'qs_json': qs_json
        })

        return context

    def post(RandomView, request, *args, **kwargs):
        # reference the post method from index view
        return IndexView.post(RandomView, request, *args, **kwargs)


class AboutView(TemplateView):
    template_name = 'dictionary/about.html'


class TosView(TemplateView):
    template_name = 'dictionary/tos.html'


class PrivacyView(TemplateView):
    template_name = 'dictionary/privacy.html'


class DmcaView(TemplateView):
    template_name = 'dictionary/dmca.html'


class ContentGuidelinesView(TemplateView):
    template_name = 'dictionary/content_guidelines.html'


class EditorView(TemplateView):
    template_name = 'dictionary/editor.html'


class BrowseView(ListView):
    """Show Terms starting with a particular character"""
    template_name = 'dictionary/browse.html'
    context_object_name = 'terms'
    paginate_by = 10

    def get_queryset(self):
        char = self.kwargs['char']
        queryset = Term.objects.filter(approved=True, word__startswith=char).annotate(
            upvotes_count=Count('upvote', distinct=True),
            downvotes_count=Count(
                'downvote', distinct=True, filter=Q(approved=True))
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        char = self.kwargs['char']
        qs_json = json.dumps(list(Term.objects.filter(approved=True).values()),
                             indent=4, sort_keys=True, default=str)

        # context["terms"] = terms
        context['char'] = char
        context['qs_json'] = qs_json
        context['form'] = LoginForm()
        return context

    def post(BrowseView, request, *args, **kwargs):
        # reference the post method from Index view
        return IndexView.post(BrowseView, request, *args, **kwargs)


class TermCreateView(CreateView):
    """This class allows a user to define a new word"""
    model = Term
    form_class = TermForm

    def form_valid(self, form):
        try:
            form.instance.author = self.request.user

            def create_meta_keywords(form):
                keywords = []

                word = form.cleaned_data['word'].split(" ")
                keywords += word

                definition = form.cleaned_data['definition'].split(" ")
                keywords += definition

                if form.cleaned_data['other_definitions']:
                    other_definitions = form.cleaned_data['other_definitions'].split(
                        " ")
                    keywords += other_definitions
                else:
                    pass

                str_keywords = ', '.join([str(word) for word in keywords])

                form.instance.meta_keywords = str_keywords

            def create_meta_description(form):
                form.instance.meta_description = form.cleaned_data['definition']

            create_meta_keywords(form)
            create_meta_description(form)

            messages.add_message(self.request, messages.SUCCESS,
                                 'Word added successfully, await approval')

            # submit form after login check submit view
        except:
            pass

        return super().form_valid(form)


class SubmitView(TemplateView):
    template_name = 'dictionary/submit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LoginForm()

        return context

    def get(self, request, *args, **kwargs):
        url = request.META['wsgi.url_scheme']
        host = request.get_host()
        referer = f'{url}://{host}/add'
        if request.META.get('HTTP_REFERER') == referer:
            return render(request, 'dictionary/submit.html', self.get_context_data())
        else:
            return HttpResponse('Page Access denied')

    def post(self, request, *args, **kwargs):
        # check if cookies are working on browser
        request.session.set_test_cookie()

        # Check that the test cookie worked
        if request.session.test_cookie_worked():
            # delete the test cookie
            request.session.delete_test_cookie()

            request.session['submit'] = True

            # retrieve post data
            word = request.POST.get('word')
            definition = request.POST.get('definition')
            example = request.POST.get('example')
            example_translation = request.POST.get('example_translation')
            other_definitions = request.POST.get('other_definitions')
            language = request.POST.get('language')
            dialect = request.POST.get('dialect')

            # assign data to cookie
            request.session['word'] = word
            request.session['definition'] = definition
            request.session['example'] = example
            request.session['example_translation'] = example_translation
            request.session['other_definitions'] = other_definitions
            request.session['language'] = language
            request.session['dialect'] = dialect
        else:
            return HttpResponse("Please unblock cookies to continue")

        return render(request, 'dictionary/submit.html', self.get_context_data())


class TermDetailView(DetailView):
    model = Term

    def get_object(self):
        queryset = Term.objects.annotate(
            upvotes_count=Count('upvote', distinct=True),
            downvotes_count=Count(
                'downvote', distinct=True,)
        )
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs_json = json.dumps(list(Term.objects.filter(approved=True).values()),
                             indent=4, sort_keys=True, default=str)

        context['qs_json'] = qs_json
        context['form'] = LoginForm()

        return context

    def post(TermDetailView, request, *args, **kwargs):
        # reference the post method from Index view
        return IndexView.post(TermDetailView, request, *args, **kwargs)


class TermUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """ view to update word definitions"""
    model = Term
    form_class = TermForm

    def test_func(self):
        user = self.request.user
        term = self.get_object()
        usergroup = None
        usergroup = self.request.user.groups.values_list(
            'name', flat=True).first()
        if usergroup == 'Editor' or term.author == user:
            return True
        return False

    def form_valid(self, form):
        try:

            def create_meta_keywords(form):
                keywords = []

                word = form.cleaned_data['word'].split(" ")
                keywords += word

                definition = form.cleaned_data['definition'].split(" ")
                keywords += definition

                if form.cleaned_data['other_definitions']:
                    other_definitions = form.cleaned_data['other_definitions'].split(
                        " ")
                    keywords += other_definitions
                else:
                    pass

                str_keywords = ', '.join([str(word) for word in keywords])

                form.instance.meta_keywords = str_keywords

            def create_meta_description(form):
                form.instance.meta_description = form.cleaned_data['definition']

            create_meta_keywords(form)
            create_meta_description(form)

            messages.add_message(self.request, messages.SUCCESS,
                                 'Word updated successfully')
        except:
            messages.add_message(self.request, messages.ERROR,
                                 'Word updating failed, try again later!')
        # Add functionality to riderect to review page on referal
        return super().form_valid(form)


class TermDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Term

    def get_success_url(self):
        messages.add_message(self.request, messages.INFO,
                             'Word deleted successfully')
        return reverse('index')

    def test_func(self):
        user = self.request.user
        term = self.get_object()
        if user.is_staff or term.author == user:
            return True
        return False

# handle 404 error requests


def error_404(request, exception):
    return render(request, 'errors/404.html')


def error_500(request, exception=None):
    return render(request, 'errors/500.html')

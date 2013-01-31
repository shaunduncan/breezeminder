from flask import (flash,
                   redirect,
                   render_template,
                   request,
                   url_for)
from flask.ext.login import (current_user,
                             fresh_login_required)

from breezeminder.app import app
from breezeminder.forms.reminder import ReminderForm, ReminderType
from breezeminder.models.reminder import Reminder, ReminderHistory
from breezeminder.util.pagination import Paginator
from breezeminder.util.views import nocache


@fresh_login_required
@nocache
def reminders():
    ctx = {
        'title': 'Manage Your Reminders',
        'description': 'Manage reminders for your MARTA Breeze cards',
        'reminders': Reminder.objects.filter(owner=current_user._get_current_object())
    }
    return render_template('user/reminders/index.html', **ctx)


@fresh_login_required
@nocache
def delete_reminder(pk_hash):
    reminder = Reminder.objects.get_or_404(pk_hash=pk_hash,
                                           owner=current_user._get_current_object())
    reminder.delete()
    flash('Reminder deleted successfully', 'success')
    return redirect(url_for('user.reminders'))


@fresh_login_required
@nocache
def reminder_history(pk_hash):
    reminder = Reminder.objects.get_or_404(pk_hash=pk_hash,
                                           owner=current_user._get_current_object())
    history = ReminderHistory.objects.filter(reminder=reminder)

    # Paginate
    try:
        history = Paginator(history, page=int(request.args.get('page', 1)))
    except (IndexError, ValueError):
        return redirect(url_for('user.reminders.history', pk_hash=reminder.pk_hash))

    context = {
        'title': 'Reminder History',
        'description': 'View Reminder Sent History',
        'reminder': reminder,
        'history': history
    }

    return render_template('user/reminders/history/index.html', **context)


@fresh_login_required
@nocache
def view_history(pk_hash):
    record = ReminderHistory.objects.get_or_404(pk_hash=pk_hash,
                                                owner=current_user._get_current_object())

    context = {
        'title': 'Reminder History Details',
        'description': 'Full reminder details',
        'record': record
    }

    return render_template('user/reminders/history/view.html', **context)


@fresh_login_required
@nocache
def edit_reminder(pk_hash):
    reminder = Reminder.objects.get_or_404(pk_hash=pk_hash,
                                           owner=current_user._get_current_object())

    form = ReminderForm(request.form)
    if request.method == 'POST':
        if form.validate():
            try:
                was_changed = form.is_changed_from(reminder)
                reminder = form.populate_reminder(reminder)
                reminder.save()

                # We need to check for new reminders only if changed
                if was_changed:
                    reminder.check_all_cards(force=True)

                flash('Reminder saved successfully', 'success')
            except ReminderType.DoesNotExist:
                flash('We currently support the type of reminder you are trying to create', 'error')

            return redirect(url_for('user.reminders'))
    else:
        form = ReminderForm.from_reminder(reminder)

    # Get cards that have been reminded
    reminder_log = reminder.last_reminded()

    context = {
        'title': 'Edit Reminder',
        'description': 'Edit Reminder for your MARTA Breeze Card',
        'form': form,
        'type_help': ReminderType.objects.all_tuples(field='description'),
        'reminder': reminder,
        'reminder_log': reminder_log
    }
    return render_template('user/reminders/edit.html', **context)


@fresh_login_required
@nocache
def add_reminder():
    form = ReminderForm(request.form)

    if request.method == 'POST':
        if form.validate():
            try:
                reminder = form.populate_reminder(Reminder())
                reminder.owner = current_user._get_current_object()
                reminder.save()

                # We need to check for new reminders
                reminder.check_all_cards(force=True)

                flash('Reminder created successfully', 'success')
            except ReminderType.DoesNotExist:
                flash('We currently support the type of reminder you are trying to create', 'error')

            return redirect(url_for('user.reminders'))

    context = {
        'title': 'Add Reminder',
        'description': 'Add a new reminder for your MARTA Breeze Card',
        'form': form,
        'type_help': ReminderType.objects.all_tuples(field='description'),
    }
    return render_template('user/reminders/add.html', **context)


app.add_url_rule('/reminders/', 'user.reminders', reminders)
app.add_url_rule('/reminders/delete/<pk_hash>', 'user.reminders.delete', delete_reminder)
app.add_url_rule('/reminders/history/<pk_hash>', 'user.reminders.history', reminder_history)
app.add_url_rule('/reminders/history/details/<pk_hash>', 'user.reminders.history.view', view_history)
app.add_url_rule('/reminders/edit/<pk_hash>', 'user.reminders.edit', edit_reminder, methods=['GET', 'POST'])
app.add_url_rule('/reminders/add/', 'user.reminders.add', add_reminder, methods=['GET', 'POST'])

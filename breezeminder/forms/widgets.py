from cgi import escape

from wtforms.widgets import (HTMLString,
                             Select,
                             html_params)


class BootstrapButtonWidget(Select):
    """
    A more rich interation with what is essentially a checkbox or radio. This
    also works for select fields or select multiple fields since the expectation of
    either is to work like a radio or checkbox respectively. For that reason, this
    widget inherits from `wtforms.widgets.Select`.

    Since this implementation uses a series of button elements as set with Twitter
    Bootstrap (http://twitter.github.com/bootstrap/javascript.html#buttons), this
    widget must tie in hidden form inputs to match the state. Javascript handles 
    button clicks to update this state. The expectation is that for radio selects
    there will be only a single hidden element while checkboxes may have several.
    """

    def __init__(self, *args, **kwargs):
        self.btn_class = kwargs.pop('btn_class', '') 
        super(BootstrapButtonWidget, self).__init__(*args, **kwargs)

    def __call__(self, field, **kwargs):
        kwargs['data-toggle'] = 'buttons-checkbox' if self.multiple else 'buttons-radio'

        classes = [
            'btn-group',
            kwargs.get('class', '')
        ]

        kwargs['class'] = ' '.join(classes).replace('  ', ' ').strip()
        kwargs['data-toggle-name'] = '%s' % field.name

        html = ['<div %s>' % html_params(**kwargs)]

        for val, label, selected in field.iter_choices():
            html.append(self.render_option(val, label, selected, btn_class=self.btn_class))

        html.append('</div>')

        for val, label, selected in field.iter_choices():
            if selected:
                html.append('<input type="hidden" id="opt-%s-%s" name="%s" value="%s"></input>' % \
                        (field.name, val, field.name, val))

        # This bit of javascript ensures that the backend form elements are written to. And this
        # happens regardless of the widget implementation (checkbox/radio). Nice!
        js = """
<script type="text/javascript">
    $('div[data-toggle-name=%s] button').click(function() {
        var that = this;

        setTimeout(function() {
            var container = $(that).parent();
            var hidden_id_pat = 'opt-' + container.attr('data-toggle-name') + '-';

            $('input[id^=' + hidden_id_pat + ']').remove();

            container.children('button').each(function() {
                var btn = $(this);
                var hidden_id = 'opt-' + container.attr('data-toggle-name') + '-' + btn.val();
                
                if(btn.hasClass('active'))
                {
                    container.after('<input type="hidden" id="' + hidden_id + '" '
                        + 'name="' + container.attr('data-toggle-name') + '" '
                        + '" value="' + btn.val() + '" />');
                }
            });
        },1);
    });
</script>""" % kwargs['data-toggle-name']

        html.append(js)
        
        return HTMLString(''.join(html))

    @classmethod
    def render_option(cls, value, label, selected, **kwargs):
        options = dict(kwargs, value=value)

        classes = [
            'btn',
            'active' if selected else '',
            options.pop('btn_class', ''),
            options.get('class', '')
        ]

        options['class'] = ' '.join(classes).replace('  ', ' ').strip()
        options['type'] = 'button'
        return HTMLString('<button %s>%s</button>' % (html_params(**options), escape(unicode(label))))

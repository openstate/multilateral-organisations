from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import SelectField, SubmitField


class SelectionForm(FlaskForm):
    country = SelectField('Country', validators=[DataRequired()])

    value_type = SelectField(
        'Value type',
        choices=[
            ('sum', 'total amount'),
            ('len', 'number of transactions')
        ],
        validators=[DataRequired()]
    )

    num_or_perc = SelectField(
        'Number or percentage',
        choices=[
            ('numbers', 'numbers'),
            ('percentages', 'percentages')
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField(
        'Go',
        render_kw={
            'class': 'btn btn-info'
        }
    )

import argparse
import csv
import datetime
import sys
import random
import smtplib


class Person(object):
    FIELDS = ['name', 'email', 'favorite_color', 'address', 'restrictions',
              'functional_or_frivolous', 'keepsake_or_consumable', 'tshirt_size_etc',
              'interview_responses', 'msg_to_santa', 'msg_to_lucia', 'reveal_receiving',
              'reveal_giving', 'recipient']

    def __init__(self, **kwargs):
        # these fields are easy to handle
        self.name = kwargs['Name']
        self.email = kwargs['Email']
        self.favorite_color = kwargs.get('Favorite color?', '')

        # these ones are a little harder, but all pretty similar
        for key, value in kwargs.items():
            if key.startswith('Address'):
                self.address = value
            elif key.startswith('Allergies'):
                self.restrictions = value
            elif key.startswith('Do you prefer functional'):
                self.functional_or_frivolous = value
            elif key.startswith('Do you like keepsakes'):
                self.keepsake_or_consumable = value
            elif key.startswith('What size t-shirt'):
                self.tshirt_size_etc = value
            elif key.startswith("You're doing a job interview"):
                self.interview_responses = value
            elif key.startswith('General message for your'):
                self.msg_to_santa = value
            elif key.startswith('General message for ME'):
                self.msg_to_lucia = value
            elif key.startswith('Opt-in name reveal - RECEIVING'):
                self.reveal_receiving = value.startswith('YES')
            elif key.startswith('Opt-in name reveal - GIVING'):
                self.reveal_giving = value.startswith('YES')

        # populated later!
        self.recipient = None

    def to_dict(self):
        data = {field: getattr(self, field) for field in self.FIELDS}
        data['recipient'] = self.recipient.name
        return data

    def knows_recipient_identity(self):
        return self.reveal_giving or self.recipient.reveal_receiving


def read_data_from_google_form_csv(filename):
    with open(filename, newline='') as f:
        reader = csv.DictReader(f)
        return [Person(**dict(row)) for row in reader]


def set_gift_giving_order(people):
    random.shuffle(people)
    for i in range(len(people) - 1):
        people[i].recipient = people[i + 1]
    people[-1].recipient = people[0]


def write_reference_data(rows, filename=None):
    """
    Writes a CSV file with output that we can reference at our leisure
    """
    filename = filename or f"output_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    fieldnames = Person.FIELDS
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate_email_attachment(giver, filename=None, reveal_address=False):
    filename = filename or giver.email or giver.name
    with open(filename, 'w') as f:
        for key, value in giver.recipient.to_dict().items():
            if key in ['recipient', 'msg_to_lucia', 'reveal_receiving', 'reveal_giving']:
                # they don't need to know..
                continue
            if key in ['name', 'email'] and not giver.knows_recipient_identity():
                # they don't need to know.......
                continue
            if key == 'address' and not giver.knows_recipient_identity() and not reveal_address:
                # they don't need to know...yet
                continue
            f.write(f'{key}: {value}\n')


def main(argv=sys.argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='input_file', required=True)
    args = parser.parse_args(argv[1:])

    people = read_data_from_google_form_csv(args.input_file)
    set_gift_giving_order(people)

    output_data = [p.to_dict() for p in people]
    write_reference_data(output_data)

    for person in people:
        generate_email_attachment(person, reveal_address=True)


if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))
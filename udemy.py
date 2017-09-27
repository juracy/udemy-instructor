#!/usr/bin/env python3

import sys
import os
import requests

PAGE_SIZE = os.getenv('UDEMY_FETCH', 500)


class Aggregate(object):
    def __init__(self):
        self.students = 0
        self.revenues = 0

    def __add__(self, value):
        self.students += 1
        self.revenues += value
        return self

    def __str__(self):
        return '%2d students - total: $%6.2f - average: $%6.2f' % (
            self.students, self.revenues,
            self.revenues / self.students)


class Udemy(object):
    def __init__(self):
        self.token = os.getenv('UDEMY_TOKEN')
        if not self.token:
            raise Exception('Missing token, please set environment variable: UDEMY_TOKEN')

        self.statement = os.getenv('UDEMY_STATEMENT')
        if not self.statement:
            raise Exception('Missing statement, please set environment variable: UDEMY_STATEMENT')

        self.headers = {
            'authorization': 'Bearer ' + self.token,
            'x-udemy-authorization': 'Bearer ' + self.token,
        }

    def summarize(self):
        self.totals = {}
        for sale in self.sales['data']:
            self.totals[sale['formatted_date']] = \
                self.totals.get(sale['formatted_date'], Aggregate()) + \
                sale['instructor_share']

        self.totals_refunds = sum(
            refund['instructor_refund_amount'] for refund in self.refunds['data'])

    def get_refunds(self):
        url = ('https://www.udemy.com/api-2.0/statements/{}/' +
               'refunds?page=1&page_size={}').format(self.statement, PAGE_SIZE)
        response = requests.get(url, headers=self.headers)
        self.refunds = response.json()

    def get_sales(self):
        url = ('https://www.udemy.com/api-2.0/statements/{}/' +
               'sales?page=1&page_size={}').format(self.statement, PAGE_SIZE)
        response = requests.get(url, headers=self.headers)
        self.sales = response.json()

    def display(self):
        from datetime import datetime

        print('Date: ', datetime.now())
        for date in sorted(self.totals.keys()):
            print('{}: {}'.format(date.split()[1], self.totals[date]))

        sums = sum(t.revenues for t in self.totals.values())
        students = sum(t.students for t in self.totals.values())
        print()
        print('total: {} students ${:.2f}'.format(students, sums))
        print('refunds:', '%6.2f' % self.totals_refunds)
        print('revenues:', '%6.2f' % (sums - self.totals_refunds))

        day = datetime.now().day
        print('average: {:.1f} students/day ${:.2f}/day ${:.2f}/student'.format(
                students / day, (sums - self.totals_refunds) / day,
                (sums - self.totals_refunds) / students))
        print('month preview: ${:.2f}'.format((sums - self.totals_refunds) / day * 31))


if __name__ == '__main__':
    try:
        u = Udemy()
    except Exception as e:
        print(e)
        sys.exit(1)

    u.get_sales()
    u.get_refunds()
    u.summarize()
    u.display()

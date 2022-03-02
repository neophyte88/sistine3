import json
import argparse
import random
import datetime

import matplotlib.pyplot as plt


def parse_data(data):
    with open(data, "r") as f:
        return json.load(f)


def make_line_chart(args):
    data = parse_data(args.data)
    plt.plot(range(len(data)), data)
    plt.title(args.title)
    plt.savefig(args.output)


def make_pie_chart(args):
    data = parse_data(args.data)
    colors = [(random.random(), random.random(), random.random()) for _ in range(len(data))]
    labels = list(set(data))
    counts = [data.count(x) for x in labels]
    plt.title(args.title)
    plt.pie(counts, labels=labels, colors=colors, autopct='%1.1f%%')
    plt.axis("equal")
    plt.savefig(args.output)


def make_timeseries_chart(args):
    data = parse_data(args.data)
    data = [(x[0], datetime.datetime.strptime(x[1], "%Y-%m-%d %H:%M:%S")) for x in data]
    data.sort(key=lambda x: x[1])

    values = [x[0] for x in data]
    timestamps = [x[1] for x in data]

    plt.title(args.title)
    plt.plot(timestamps, values)
    plt.savefig(args.output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--chart_type", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", required=True)

    args = parser.parse_args()

    if args.chart_type == "line":
        make_line_chart(args)
    elif args.chart_type == "pie":
        make_pie_chart(args)
    elif args.chart_type == "timeseries":
        make_timeseries_chart(args)
    else:
        exit(-1)

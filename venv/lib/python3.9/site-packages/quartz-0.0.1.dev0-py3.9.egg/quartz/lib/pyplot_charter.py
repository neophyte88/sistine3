import base64
import json
import sys
import subprocess
import os
import uuid

import tempfile


class PyplotCharter(object):
    def __init__(self, events):
        self.events = events

    def make_plot(self, by_field, plot_type, title):
        temp_data_file_name = os.path.join(os.environ["TMP"], str(uuid.uuid4()))
        temp_data_file = open(temp_data_file_name, "w")
        temp_image_file_name = os.path.join(os.environ["TMP"], str(uuid.uuid4()) + ".png")

        if plot_type != "timeseries":
            self.preprocess_data_regular(self.events, by_field, temp_data_file)
        else:
            self.preprocess_data_with_timestamps(self.events, by_field, temp_data_file)

        temp_data_file.close()

        cmd = self.make_cmd(temp_data_file_name, temp_image_file_name, plot_type, title)
        returncode = self.run_cmd(cmd)
        if returncode != 0:
            raise RuntimeError("Chart generation failed")

        with open(temp_image_file_name, "rb") as out_img:
            image_data = base64.b64encode(out_img.read())

        # cleanup
        os.remove(temp_data_file_name)
        os.remove(temp_image_file_name)

        return image_data.decode()

    def make_cmd(self, input_file_path, output_file_path, chart_type, title):
        cmd = [
            sys.executable,
            "-m",
            "quartz.lib.utilscripts.generate_chart",
            "--data", input_file_path,
            "--output", output_file_path,
            "--chart_type", chart_type,
            "--title", title
        ]
        return cmd

    def preprocess_data_regular(self, events, by_field, temp_data_file):
        final_data = [ev["values"][by_field] for ev in events]
        json.dump(final_data, temp_data_file)

    def preprocess_data_with_timestamps(self, events, by_field, temp_data_file):
        final_data = [(ev["values"][by_field], ev["timestamp"].strfmt("%Y-%m-%d %H:%M:%S")) for ev in events]
        json.dump(final_data, temp_data_file)

    def run_cmd(self, cmd):
        proc = subprocess.Popen(cmd)
        proc.wait()
        return proc.returncode


if __name__ == '__main__':
    image_data = PyplotCharter([]).make_plot("", "line", "hello there")

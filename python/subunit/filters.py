#  subunit: extensions to python unittest to get test results from subprocesses.
#  Copyright (C) 2009  Robert Collins <robertc@robertcollins.net>
#
#  Licensed under either the Apache License, Version 2.0 or the BSD 3-clause
#  license at the users choice. A copy of both licenses are available in the
#  project source as Apache-2.0 and BSD. You may not use this file except in
#  compliance with one of these two licences.
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under these licenses is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
#  license you chose for the specific language governing permissions and
#  limitations under that license.
#


from optparse import OptionParser
import sys

from subunit import DiscardStream, ProtocolTestCase
from subunit.test_results import CsvResult


def make_options():
    parser = OptionParser(description=__doc__)
    parser.add_option(
        "--no-passthrough", action="store_true",
        help="Hide all non subunit input.", default=False, dest="no_passthrough")
    parser.add_option(
        "-o", "--output-to",
        help="Output the XML to this path rather than stdout.")
    parser.add_option(
        "-f", "--forward", action="store_true", default=False,
        help="Forward subunit stream on stdout.")
    return parser


def run_tests_from_stream(input_stream, result, passthrough_stream=None,
                          forward_stream=None):
    """Run tests from a subunit input stream through 'result'.

    :param input_stream: A stream containing subunit input.
    :param result: A TestResult that will receive the test events.
    :param passthrough_stream: All non-subunit input received will be
        sent to this stream.  If not provided, uses the ``TestProtocolServer``
        default, which is ``sys.stdout``.
    :param forward_stream: All subunit input received will be forwarded
        to this stream.  If not provided, uses the ``TestProtocolServer``
        default, which is to not forward any input.
    :return: True if the test run described by ``input_stream`` was
        successful.  False otherwise.
    """
    test = ProtocolTestCase(
        input_stream, passthrough=passthrough_stream,
        forward=forward_stream)
    result.startTestRun()
    test.run(result)
    result.stopTestRun()
    return result.wasSuccessful()


def filter_by_result(result_factory, output_path, no_passthrough, forward,
                     input_stream=sys.stdin):
    """Filter an input stream using a test result.

    :param result_factory: A callable that when passed an output stream
        returns a TestResult.  It is expected that this result will output
        to the given stream.
    :param output_path: A path send output to.  If None, output will be go
        to ``sys.stdout``.
    :param no_passthrough: If True, all non-subunit input will be discarded.
        If False, that input will be sent to ``sys.stdout``.
    :param forward: If True, all subunit input will be forwarded directly to
        ``sys.stdout`` as well as to the ``TestResult``.
    :param input_stream: The source of subunit input.  Defaults to
        ``sys.stdin``.
    :return: 0 if the input represents a successful test run, 1 if a failed
        test run.
    """
    if no_passthrough:
        passthrough_stream = DiscardStream()
    else:
        passthrough_stream = None

    if forward:
        forward_stream = sys.stdout
    else:
        forward_stream = None

    if output_path is None:
        output_to = sys.stdout
    else:
        output_to = file(output_path, 'wb')

    try:
        result = result_factory(output_to)
        was_successful = run_tests_from_stream(
            input_stream, result, output_to, passthrough_stream,
            forward_stream)
    finally:
        if output_path:
            output_to.close()
    if was_successful:
        return 0
    else:
        return 1


def main(result_factory):
    parser = make_options()
    (options, args) = parser.parse_args()
    sys.exit(
        filter_by_result(
            CsvResult, options.output_to, options.no_passthrough,
            options.forward))

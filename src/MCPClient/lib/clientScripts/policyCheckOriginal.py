#!/usr/bin/env python2
from __future__ import print_function
import sys
from custom_handlers import get_script_logger
from policyCheck import PolicyChecker


class OriginalPolicyChecker(PolicyChecker):

    purpose = 'checkingOriginalPolicy'

    def we_check_this_type_of_file(self):
        # During transfer we check all files. Is this correct or are there
        # classes of file that we do not want to perform policy checks on?
        return True


if __name__ == '__main__':
    logger = get_script_logger(
        "archivematica.mcp.client.policyCheckOriginal")
    file_path = sys.argv[1]
    file_uuid = sys.argv[2]
    sip_uuid = sys.argv[3]
    shared_path = sys.argv[4]
    policy_checker = OriginalPolicyChecker(file_path, file_uuid, sip_uuid,
                                           shared_path)
    sys.exit(policy_checker.check())

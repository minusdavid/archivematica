# -*- coding: utf-8 -*-
"""Migration for PID Binding: persistent identifier creation & resolution.

# UNUSED and TO-BE-DEPRECATED: keeping around in case I need to backtrack.
# Chain Link after #1 is "Normalize: Normalize for preservation"
# Its UUID is 440ef381-8fe8-4b6e-9198-270ee5653454.
after_cl_1_uuid = normalize_preservation_chain_link_uuid = (
    '440ef381-8fe8-4b6e-9198-270ee5653454')
after_cl_1 = normalize_preservation_chain_link = (
    MicroServiceChainLink.objects.get(
        id=normalize_preservation_chain_link_uuid))

# Chain Link after #2 is "Normalize: Set file permissions
# Its UUID is 83257841-594d-4a0e-a4a1-1e9269c30f3d.
after_cl_2_uuid = set_file_permissions_chain_link_uuid = (
    '83257841-594d-4a0e-a4a1-1e9269c30f3d')
after_cl_2 = set_file_permissions_chain_link = (
    MicroServiceChainLink.objects.get(
        id=set_file_permissions_chain_link_uuid)
"""

from __future__ import print_function, unicode_literals

from django.db import migrations, models


def data_migration(apps, schema_editor):
    """Persistent Identifiers (PID) Workflow modifications (migration).
    This migration modifies the workflow so that there are two new
    micro-services, i.e., chain links, one which asks the user whether to
    bind PIDs and the another which actually binds PIDs. Binding a PID means
    requesting from a Handle server a PID (a.k.a. a "handle") for a file,
    directory or unit, and requesting that the PID be bound (set to resolve to)
    a specific external URL. Note that the PURL (i.e., PID's URL) may be
    configured to resolve to different external (resolve) URLs depending on the
    qualifier (GET query parameter) that is appended to it. See
    archivematicaCommon/lib/bindpid.py for more details.

    Creation steps:

    1. Create new Micro-service chain link "Bind PIDs"
    2. Create new Micro-service *choice* chain link "Bind PIDs?"

    Positioning steps:

    1. Position "Bind PIDs" after "Bind PIDs?", which is after "Normalize for
       access".
    """

    ###########################################################################
    # Model Classes
    ###########################################################################

    TaskType = apps.get_model('main', 'TaskType')
    TaskConfig = apps.get_model('main', 'TaskConfig')
    MicroServiceChainLink = apps.get_model('main', 'MicroServiceChainLink')
    MicroServiceChainLinkExitCode = apps.get_model(
        'main', 'MicroServiceChainLinkExitCode')
    MicroServiceChoiceReplacementDic = apps.get_model(
        'main', 'MicroServiceChoiceReplacementDic')
    StandardTaskConfig = apps.get_model('main', 'StandardTaskConfig')

    ###########################################################################
    # Useful Model Instances
    ###########################################################################

    # This is the "get replacement dic from user choice" TaskType.
    repl_dic_usr_choice_task_type = TaskType.objects.get(
        description='get replacement dic from user choice')

    # This is the TaskType that handles client scripts that work on one file at
    # a time.
    each_file_task_type = TaskType.objects.get(
        description='for each file')

    # This is the TaskType that handles client scripts that treat an entire
    # directory (i.e., Transfer) in one go.
    # TODO: use this if adding another link for binding PIDs for units and
    # directories, which seems will be necessary.
    entire_directory_task_type = TaskType.objects.get(
        description='one instance')

    # We need to position the two "Bind PIDs" chain links so that:
    # - "Generate AIP METS" comes before, and
    # - "Check if DIP should be generated" comes after.

    # Chain Link after is "Check if DIP should be generated"
    # Its UUID is f1e286f9-4ec7-4e19-820c-dae7b8ea7d09
    after_cl_uuid = 'f1e286f9-4ec7-4e19-820c-dae7b8ea7d09'
    after_cl = MicroServiceChainLink.objects.get(id=after_cl_uuid)

    # Chain Link before is "Generate AIP METS"
    # Its UUID is ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0
    before_cl_uuid = 'ccf8ec5c-3a9a-404a-a7e7-8f567d3b36a0'
    before_cl = MicroServiceChainLink.objects.get(id=before_cl_uuid)

    ###########################################################################
    # New Chain Links: "Bind PIDs"
    ###########################################################################

    # StandardTaskConfig that performs "Bind PIDs"
    bind_pids_stc_uuid = 'b055f0a4-75d7-4747-98fe-aab08d835403'
    StandardTaskConfig.objects.create(
        id=bind_pids_stc_uuid,
        execute='bindPID_v0.0',
        arguments=('"%fileUUID%" --bind-pids "%BindPIDs%"'),
        stdout_file='%SIPLogsDirectory%handles.log'
    )

    # TaskConfig that performs "Bind PIDs"
    bind_pids_task_cfg_uuid = '9c9e75e9-04b0-4a04-83ad-07ddf2ff9a17'
    bind_pids_task_cfg = TaskConfig.objects.create(
        id=bind_pids_task_cfg_uuid,
        tasktype=each_file_task_type,
        description='Bind PIDs',
        tasktypepkreference=bind_pids_stc_uuid,
        replaces_id=None,
    )

    # MSChainLink that performs "Bind PIDs" in the "Normalize for preservation
    # and access" chain.
    bind_pids_chain_link_uuid = '87e93d08-36e4-4c81-99a8-beea00b18400'
    bind_pids_chain_link = MicroServiceChainLink.objects.create(
        id=bind_pids_chain_link_uuid,
        microservicegroup='Bind PIDs',
        defaultexitmessage='Failed',
        currenttask=bind_pids_task_cfg,
        replaces_id=None,
        # Comes before existing "Normalize for preservation" chain link.
        defaultnextchainlink=after_cl
    )

    ###########################################################################
    # New Choice Chain Link: "Bind PIDs?"
    ###########################################################################

    # TaskConfig that asks "Bind PIDs?"
    bind_pids_choice_task_cfg_uuid = '02b44c99-f499-42d4-8742-3576c0d52804'
    bind_pids_choice_task_cfg = TaskConfig.objects.create(
        id=bind_pids_choice_task_cfg_uuid,
        tasktype=repl_dic_usr_choice_task_type,
        description='Bind PIDs?',
        tasktypepkreference=None,
        replaces_id=None,
    )

    # MSChainLink that asks "Bind PIDs?"
    bind_pids_choice_chain_link_uuid = '05357876-a095-4c11-86b5-a7fff01af668'
    bind_pids_choice_chain_link = MicroServiceChainLink.objects.create(
        id=bind_pids_choice_chain_link_uuid,
        microservicegroup='Bind PIDs',
        defaultexitmessage='Failed',
        currenttask=bind_pids_choice_task_cfg,
        replaces_id=None,
        # Comes before chain link created above
        defaultnextchainlink=bind_pids_chain_link
    )

    # Create the "No" choice, i.e., "No, do not assign UUIDs to directories".
    MicroServiceChoiceReplacementDic.objects.create(
        id='fcfea449-158c-452c-a8ad-4ae009c4eaba',
        description='No',
        replacementdic='{"%BindPIDs%": "False"}',
        choiceavailableatlink=bind_pids_choice_chain_link,
        replaces_id=None
    )

    # Create the "Yes" choice, i.e., "Yes, do assign UUIDs to directories".
    MicroServiceChoiceReplacementDic.objects.create(
        id='1e79e1b6-cf50-49ff-98a3-fa51d73553dc',
        description='Yes',
        replacementdic='{"%BindPIDs%": "True"}',
        choiceavailableatlink=bind_pids_choice_chain_link,
        replaces_id=None
    )

    ###########################################################################
    # Positioning
    ###########################################################################

    # Configure any links that exit to "Check if DIP should be generated" to
    # now exit to the "Bind PIDs?" choice link.
    MicroServiceChainLinkExitCode.objects\
        .filter(nextmicroservicechainlink=after_cl)\
        .update(nextmicroservicechainlink=bind_pids_choice_chain_link)
    MicroServiceChainLink.objects\
        .filter(defaultnextchainlink=after_cl)\
        .exclude(id=bind_pids_chain_link_uuid)\
        .update(defaultnextchainlink=bind_pids_choice_chain_link)

    # Make "Bind PIDs" exit to "Check if DIP should be generated"
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
            ('ddb8ac64-b501-4350-aa51-f7ff5b0b70e5', 0, 2),
            ('6061da26-8a89-4656-9413-0a4420220656', 1, 4)):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=bind_pids_chain_link,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=after_cl
        )

    # NEW Make "Bind PIDs?" exit to "Bind PIDs"
    # Note: in ``exit_message_codes`` 2 is 'Completed successfully' and 4 is
    # 'Failed'; see models.py.
    for pk, exit_code, exit_message_code in (
            ('6c23d182-30d4-4c39-a706-fe0fc0df6299', 0, 2),
            ('363319c1-eaf1-4bf7-ad34-1a38db4c7ca8', 1, 4)):
        MicroServiceChainLinkExitCode.objects.create(
            id=pk,
            microservicechainlink=bind_pids_choice_chain_link,
            exitcode=exit_code,
            exitmessage=exit_message_code,
            nextmicroservicechainlink=bind_pids_chain_link
        )

    # Make the ``before`` chain link exit to the "Bind PIDs?" link.
    MicroServiceChainLinkExitCode.objects.filter(
        microservicechainlink=before_cl).update(
            nextmicroservicechainlink=bind_pids_choice_chain_link)
    before_cl.defaultnextchainlink = bind_pids_choice_chain_link


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0033_dir_uuids'),
    ]

    operations = [
        # Modify the workflow:
        migrations.RunPython(data_migration),
        migrations.CreateModel(
            name='Identifier',
            fields=[
                ('id', models.AutoField(serialize=False, editable=False, primary_key=True, db_column=b'pk')),
                ('type', models.TextField(null=True, verbose_name='Identifier Type')),
                ('value', models.TextField(help_text='Used for premis:objectIdentifierType and premis:objectIdentifierValue in the METS file.', null=True, verbose_name='Identifier Value'))
            ],
            options={
                'db_table': 'Identifiers',
            },
        ),
        migrations.AddField(
            model_name='directory',
            name='identifiers',
            field=models.ManyToManyField(to='main.Identifier'),
        ),
        migrations.AddField(
            model_name='sip',
            name='identifiers',
            field=models.ManyToManyField(to='main.Identifier'),
        ),
        migrations.AddField(
            model_name='file',
            name='identifiers',
            field=models.ManyToManyField(to='main.Identifier'),
        ),
    ]

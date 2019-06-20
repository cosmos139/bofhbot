import asyncio
import bot_checks
import shlex

from termcolor import colored
from bot_analyzer import STATES

POWER_CYCLE_COMMAND = "sudo /global/home/groups/scs/sbin/ipmiwrapper.tin.sh cycle {node}"
POWER_ON_COMMAND = "sudo /global/home/groups/scs/sbin/ipmiwrapper.tin.sh on {node}"
POWER_OFF_COMMAND = "sudo /global/home/groups/scs/sbin/ipmiwrapper.tin.sh down {node}"
SLURM_RESUME_COMMAND = "sudo scontrol update node={node} state=resume"
SYSTEMCTL_DAEMON_RELOAD_COMMAND = "sudo systemctl daemon-reload"
SYSTEMCTL_START_SLURM_COMMAND = "sudo systemctl start slurmd"

def ssh(node):
    def ssh_command(command):
        return 'ssh {node} {command}'.format(node=shlex.quote(node),command=shlex.quote(command))
    return ssh_command

def power_cycle(node, state):
    return [
        POWER_CYCLE_COMMAND.format(node=node)
    ]

def power_on(node, state):
    return [
        POWER_ON_COMMAND.format(node=node)
    ]

def restart_slurm(node, state):
    return [
        ssh(node)(SYSTEMCTL_DAEMON_RELOAD_COMMAND),
        ssh(node)(SYSTEMCTL_START_SLURM_COMMAND),
    ]

def slurm_resume(node, state):
    return [
        SLURM_RESUME_COMMAND.format(node=node)
    ]

def nothing(node, state):
    return []

SUGGESTION = {
    STATES['NODE_KILLED_IPMI_ON']: power_cycle,
    STATES['NODE_KILLED_IPMI_OFF']: power_on,
    STATES['SLURM_FAILED']: restart_slurm,
    STATES['NODE_WORKING']: slurm_resume,
    STATES['UNKNOWN']: nothing
}

def suggest(node, state):
    return SUGGESTION[state](node, state)

def display_status(status):
    return str(status)

def display_suggestion(suggestion):
    return colored('\n'.join([ '\t' + command for command in suggestion ]), attrs=['bold'])

async def interactive_suggest(suggestions, status):
    accepted_nodes = []
    suggestions = { node: suggestion for node, suggestion in suggestions.items() if suggestion }
    print('{}/{} nodes have suggestions'.format(len(suggestions.keys()), len(status.keys())))
    for node, suggestion in suggestions.items():
        print(colored(node, 'green' if status[node]['SSH'] else 'red', attrs=['bold']), '-', display_status(status[node]))
        print(display_suggestion(suggestion))
        response = input(colored('Run suggestion? (y/[n]) ', 'grey', attrs=['bold']))
        if response == 'y':
            for command in suggestion:
                await asyncio.sleep(1) # bot_checks.run_local_command(suggestion)
            accepted_nodes.append(node)
            print('Accepted suggestion\n')
        else:
            print('Rejected suggestion\n')
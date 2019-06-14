# ansible for ffhb events

## Commands

## Ping
check which nodes are up by ssh
```
ansible -m sh_ping all
```

### Settings

update settings on every node
```
ansible-playbook playbooks/nodes.yml
```

update settings without vpn on every node
```
ansible-playbook playbooks/nodes.yml --skip-tags vpn
```

update hostname on every node
```
ansible-playbook playbooks/nodes.yml --tags hostname
```

update hostname on single node
```
ansible-playbook playbooks/nodes.yml --tags hostname --limit ac-mesh-7715
```

update settings on some node (which starts with _ac-mesh_)
```
ansible-playbook playbooks/nodes.yml --tags hostname --limit "ac-mesh*"
```


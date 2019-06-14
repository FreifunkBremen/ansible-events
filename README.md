# ansible for ffhb events

## Commands

update settings on every node
```
ansible-playbook playbooks/nodes.yml -i vorstrasse.yml
```

update settings without vpn on every node
```
ansible-playbook playbooks/nodes.yml -i vorstrasse.yml --skip-tags vpn
```

update hostname on every node
```
ansible-playbook playbooks/nodes.yml -i vorstrasse.yml --tags hostname
```

update hostname on single node
```
ansible-playbook playbooks/nodes.yml -i vorstrasse.yml --tags hostname --limit ac-mesh-7715
```

update settings on some node (which starts with _ac-mesh_)
```
ansible-playbook playbooks/nodes.yml -i vorstrasse.yml --tags hostname --limit "ac-mesh*"
```


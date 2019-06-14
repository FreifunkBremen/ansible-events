# ansible for ffhb events

## Commands

update settings on every node (restart wifi and vpn)
```
ansible-playbook playbooks/nodes.yml -i vorstrasse.yml
```

update settings without vpn on every node (do not restart fastd)
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


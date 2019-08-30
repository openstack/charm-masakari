# Overview

Masakari is used to provide automated instance recovery for virtual machines
(VMs) that use shared storage. It does this by performing live VM migrations to
an existing compute node when failures arise.

Masakari responds to two different failures types:

1. individual VM
1. compute node

When an entire compute node has failed all its VMs are "evacuated".

For more details see the [Automated Instance Recovery][cdg-app-masakari]
appendix in the [OpenStack Charms Deployment Guide][charms-deploy-guide].

> **Important**: Both the `masakari` and `masakari-monitors` charms are
  considered preview charms. They will become supported charms once software
  issues [LP #1728527][lp-1728527] and [LP #1839715][lp-1839715] are resolved.

<!-- LINKS -->

[lp-1728527]: https://bugs.launchpad.net/masakari-monitors/+bug/1728527
[lp-1839715]: https://bugs.launchpad.net/masakari/+bug/1839715
[cdg-app-masakari]: https://docs.openstack.org/project-deploy-guide/charm-deployment-guide/latest/app-masakari.html
[charms-deploy-guide]: https://docs.openstack.org/project-deploy-guide/charm-deployment-guide/latest/index.html

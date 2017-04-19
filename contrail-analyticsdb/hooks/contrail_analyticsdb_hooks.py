#!/usr/bin/env python

import sys

from charmhelpers.core.hookenv import (
    Hooks,
    UnregisteredHookError,
    config,
    log,
    relation_get,
    ERROR,
)

from charmhelpers.fetch import (
    apt_install,
    apt_upgrade,
    apt_update
)

from contrail_analyticsdb_utils import (
    fix_hostname,
    update_charm_status,
    CONTAINER_NAME,
)

from docker_utils import (
    add_docker_repo,
    DOCKER_PACKAGES,
    is_container_launched,
    load_docker_image,
)


PACKAGES = ["python", "python-yaml", "python-apt"]


hooks = Hooks()
config = config()


@hooks.hook()
def install():
    fix_hostname()
    apt_upgrade(fatal=True, dist=True)
    add_docker_repo()
    apt_update(fatal=False)
    apt_install(PACKAGES + DOCKER_PACKAGES, fatal=True)
    load_docker_image(CONTAINER_NAME)
    update_charm_status()


@hooks.hook("config-changed")
def config_changed():
    update_charm_status()


@hooks.hook("contrail-controller-relation-joined")
@hooks.hook("contrail-controller-relation-departed")
def controller_relation():
    update_charm_status()


@hooks.hook("contrail-analytics-relation-joined")
@hooks.hook("contrail-analytics-relation-departed")
@hooks.hook("contrail-analytics-relation-broken")
def analytics_relation():
    update_charm_status()


@hooks.hook("identity-admin-relation-changed")
@hooks.hook("identity-admin-relation-departed")
@hooks.hook("identity-admin-relation-broken")
def identity_admin_changed():
    if not relation_get("service_hostname"):
        log("Keystone relation not ready")
    update_charm_status()


@hooks.hook("update-status")
def update_status():
    update_charm_status(update_config=False)


@hooks.hook("upgrade-charm")
def upgrade_charm():
    if is_container_launched(CONTAINER_NAME):
        log("Container already launched", ERROR)
        # TODO: set error status?
        return

    # NOTE: image can not be deleted if container is running.
    load_docker_image(CONTAINER_NAME)
    # TODO: this hook can be fired when resource changed or charm code changed
    # so if code changed then we may need to update config
    update_charm_status()


@hooks.hook("start")
@hooks.hook("stop")
def todo():
    # TODO: think about it
    pass


def main():
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log("Unknown hook {} - skipping.".format(e))


if __name__ == "__main__":
    main()

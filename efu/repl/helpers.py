# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License
"""EFU REPL helper functions.

Includes reusable prompts, auto-completers, constraint checkers.
"""

import sys
from functools import partial

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys

from ..core.options import MODES, Option
from ..core.package import ACTIVE_INACTIVE_MODES
from ..core.package import MODES as PKG_MODES
from ..utils import indent

from .completers import (
    ObjectFilenameCompleter, ObjectModeCompleter, ObjectOptionCompleter,
    ObjectOptionValueCompleter, ObjectUIDCompleter, YesNoCompleter,
    PackageModeCompleter, ActiveInactiveCompleter)
from .validators import (
    FileValidator, ObjectUIDValidator, ContainerValidator,
    ObjectOptionValueValidator, PackageUIDValidator, YesNoValidator)


manager = KeyBindingManager.for_prompt()


@manager.registry.add_binding(Keys.ControlD)
def ctrl_d(event):
    """Ctrl D quits appliaction returning 0 to sys."""
    event.cli.run_in_terminal(sys.exit(0))


@manager.registry.add_binding(Keys.ControlC)
def ctrl_c(event):
    """Ctrl C quits appliaction returning 1 to sys."""
    event.cli.run_in_terminal(sys.exit(1))


prompt = partial(prompt, key_bindings_registry=manager.registry)


def check_arg(ctx, msg):
    """Checks if user has passed an argument.

    :param msg: The error message to display to the user in when an
                argument is not passed.
    """
    if ctx.arg is None:
        raise ValueError(msg)


def check_version(ctx):
    """Checks if package already has a version."""
    if ctx.package.version is None:
        raise ValueError('You need to set a version first')


def check_product(ctx):
    """Checks if product is already set."""
    if ctx.package.product is None:
        raise ValueError('You need to set a product first')


def set_product_prompt(product):
    """Sets prompt to be 'efu [product]'."""
    return '[{}] efu> '.format(product[:6])


def get_object_options(obj):
    """Returns the possbile options for a given object."""
    mode = MODES[obj.mode]
    options = {option.verbose_name: option for option in mode}
    # hack to let user update object filename
    options['filename'] = Option({'metadata': 'filename'})
    return options


def parse_prompt_object_uid(value):
    """Parses value passed to a prompt using get_objects_completer.

    :param value: A value returned by :func:`get_objects_completer`.
    """
    return int(value.split('#')[0].strip())


def prompt_object_options(mode):
    """Prompts user for object options.

    :param mode: A string indicating the object mode.
    """
    options = {}
    for option in MODES[mode]:
        try:
            option.validate_requirements(options)
        except ValueError:
            continue  # requirements not satisfied, skip this option
        options[option.metadata] = prompt_object_option_value(option, mode)
    return options


def prompt_object_filename(msg=None, indent_level=0):
    """Prompts user for a valid filename.

    :param msg: The prompt message to display to user.
    :param indent_level: Controls how many spaces must be added before
                         `msg`.
    """
    msg = 'Choose a file to add into your package' if msg is None else msg
    msg = indent(msg, indent_level, all_lines=True)
    msg = '{}: '.format(msg)
    completer = ObjectFilenameCompleter()
    validator = FileValidator()
    filename = prompt(msg, completer=completer, validator=validator)
    return filename.strip()


def prompt_object_mode():
    """Prompts user for a object mode."""
    msg = 'Choose a mode: '
    completer = ObjectModeCompleter()
    validator = ContainerValidator('mode', list(MODES))
    mode = prompt(msg, completer=completer, validator=validator)
    return mode.strip()


def prompt_object_uid(package, index):
    """Prompts user for an object UID.

    :param index: The object index within an object list.
    """
    msg = 'Select an object: '
    completer = ObjectUIDCompleter(package, index)
    validator = ObjectUIDValidator()
    value = prompt(msg, completer=completer, validator=validator)
    return parse_prompt_object_uid(value.strip())


def prompt_object_option(obj):
    """Prompts user for a valid option for the given object.

    :param obj: an efu `Object` instance.
    """
    options = get_object_options(obj)
    msg = 'Choose an option: '
    completer = ObjectOptionCompleter(options)
    validator = ContainerValidator('option', options)
    option = prompt(msg, completer=completer, validator=validator)
    return options[option.strip()]


def prompt_object_option_value(option, mode, indent_level=0):
    """Given an object and an option, prompts user for a valid value.

    :param option: an efu `Option` instance.
    :param mode: a valid Object mode string.
    :param indent_level: Controls how many spaces must be added before
                         `msg`.
    """
    if option.metadata == 'filename':
        return prompt_object_filename('Select a new file', indent_level=2)

    # Message
    if option.default is not None:
        default = option.default
        if option.type == 'bool':
            if default:
                default = 'Y/n'
            else:
                default = 'y/N'
        msg = '{} [{}]'.format(option.verbose_name.title(), default)
    else:
        msg = '{}'.format(option.verbose_name.title())
    msg = indent(msg, indent_level, all_lines=True)
    msg = '{}: '.format(msg)

    # Completer
    if option.choices:
        completer = ObjectOptionValueCompleter(option)
    elif option.type == 'bool':
        completer = YesNoCompleter()
    else:
        completer = None

    validator = ObjectOptionValueValidator(option, mode)

    value = prompt(msg, completer=completer, validator=validator).strip()
    value = value if value != '' else option.default
    return option.convert(value)


def prompt_package_uid():
    """Prompts user for a package UID."""
    msg = 'Type a package UID: '
    validator = PackageUIDValidator()
    uid = prompt(msg, validator=validator)
    return uid.strip()


def prompt_pull():
    """Prompts user to set if a pull should download all files or not."""
    msg = 'Should we download all files [Y/n]?:  '
    completer = YesNoCompleter()
    validator = YesNoValidator()
    answer = prompt(msg, completer=completer, validator=validator)
    return {'y': True, 'n': False}[answer.strip().lower()[0]]


def prompt_installation_set(package, msg=None, all_sets=True):
    """Prompts user for a valid installation set.

    :param package: A core.package.Package instance.
    :param msg: The prompt message to display to user.
    :param all_sets: If True, allow to select an empty installation set.
    """
    if package.objects.is_single():
        return None

    # Pre-validation
    objects = [(index, objs) for index, objs in enumerate(package.objects)]
    if not all_sets:
        objects = [(index, objs) for index, objs in objects if objs]
        if len(objects) == 0:
            raise ValueError('There is no object to operate.')
        if len(objects) == 1:
            index, _ = objects[0]
            return index
    indexes = [str(i) for i, _ in objects]

    msg = msg if msg is not None else 'Select an installation set: '
    completer = WordCompleter(indexes)
    validator = ContainerValidator('installation set', indexes)
    installation_set = prompt(msg, completer=completer, validator=validator)
    return int(installation_set.strip())


def prompt_package_mode():
    """Prompts for a valid package mode."""
    msg = 'Choose a package mode [{}]: '.format('/'.join(PKG_MODES))
    completer = PackageModeCompleter()
    validator = ContainerValidator('mode', PKG_MODES)
    mode = prompt(msg, completer=completer, validator=validator)
    return mode.strip().lower()


def prompt_active_inactive_backend():
    """Prompts for a valid active inactive backend."""
    msg = 'Choose an active inactive backend: '
    completer = ActiveInactiveCompleter()
    validator = ContainerValidator('backend', ACTIVE_INACTIVE_MODES)
    backend = prompt(msg, completer=completer, validator=validator)
    return backend.strip().lower()

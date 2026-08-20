# -*- coding: utf-8 -*-
"""Display the Design Options relevant to the active view.

Shows every Design Option Set / Design Option in the project, which
option is primary, which option is currently active for editing, and
how many elements of the active view belong to each option. The panel
stays open (modeless) and refreshes automatically when the active view
changes, or on demand with the Refresh button.
"""
#pylint: disable=import-error,invalid-name,broad-except

import os.path as op

from Autodesk.Revit.DB import (
    BuiltInCategory,
    BuiltInParameter,
    FilteredElementCollector,
    DesignOption,
    ElementDesignOptionFilter,
)

from pyrevit import framework
from pyrevit import UI
from pyrevit import forms, script

__title__ = 'View\nD.O. Panel'
__author__ = 'pyRevit'
__doc__ = 'Dockable-style panel that displays the active view\'s ' \
          'Design Option Set / Design Option settings.'
__persistentengine__ = True

logger = script.get_logger()

XAML_FILE = op.join(op.dirname(__file__), 'ViewDOPanel.xaml')


class DesignOptionRow(object):
    """Single row of data shown in the panel grid."""

    def __init__(self, option_set, option_name, is_primary,
                 is_active, element_count):
        self.OptionSet = option_set
        self.OptionName = option_name
        self.Primary = 'Yes' if is_primary else ''
        self.Active = 'Yes' if is_active else ''
        self.ElementCount = element_count


def collect_design_option_rows(doc, view):
    """Build the list of DesignOptionRow for the given view."""
    rows = []
    if not doc or not view:
        return rows

    active_option_id = DesignOption.GetActiveDesignOptionId(doc)

    # Design Option Sets have no dedicated API class - they are plain
    # Elements under the OST_DesignOptionSets category.
    option_sets = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_DesignOptionSets)\
        .WhereElementIsNotElementType()\
        .ToElements()
    option_set_names = {os_.Id: os_.Name for os_ in option_sets}

    all_options = FilteredElementCollector(doc)\
        .OfClass(DesignOption)\
        .ToElements()

    # group options by their parent option set, then sort for stable display
    options_by_set = {}
    for option in all_options:
        set_id_param = option.get_Parameter(
            BuiltInParameter.OPTION_SET_ID)
        set_id = set_id_param.AsElementId() if set_id_param else None
        set_name = option_set_names.get(set_id, 'Unknown Option Set')
        options_by_set.setdefault(set_name, []).append(option)

    for set_name in sorted(options_by_set.keys()):
        options = sorted(options_by_set[set_name], key=lambda x: x.Name)
        for option in options:
            try:
                count = FilteredElementCollector(doc, view.Id)\
                    .WherePasses(ElementDesignOptionFilter(option.Id))\
                    .WhereElementIsNotElementType()\
                    .GetElementCount()
            except Exception as count_ex:
                logger.dev_log(
                    'collect_design_option_rows::count', str(count_ex))
                count = 0

            rows.append(
                DesignOptionRow(
                    set_name,
                    option.Name,
                    option.IsPrimary,
                    active_option_id == option.Id,
                    count
                )
            )

    return rows


class ViewDOPanelWindow(forms.WPFWindow):
    """Modeless window that displays the active view's Design Options."""

    def __init__(self, xaml_file, uiapp):
        forms.WPFWindow.__init__(self, xaml_file)
        self.uiapp = uiapp

        self._view_activated_handler = framework.EventHandler[
            UI.Events.ViewActivatedEventArgs](self.on_view_activated)
        self.uiapp.ViewActivated += self._view_activated_handler

        self.Closed += self.on_closed

        self.refresh()

    def refresh_click(self, sender, args):    #pylint: disable=unused-argument
        self.refresh()

    def on_view_activated(self, sender, args):    #pylint: disable=unused-argument
        self.refresh()

    def on_closed(self, sender, args):    #pylint: disable=unused-argument
        try:
            self.uiapp.ViewActivated -= self._view_activated_handler
        except Exception as unsub_ex:
            logger.dev_log('on_closed::unsubscribe', str(unsub_ex))

    def refresh(self):
        uidoc = self.uiapp.ActiveUIDocument
        if not uidoc:
            self.tb_viewname.Text = '—'
            self.tb_status.Text = 'No active document.'
            self.grid_options.ItemsSource = []
            return

        doc = uidoc.Document
        view = uidoc.ActiveView

        self.tb_viewname.Text = view.Name if view else '—'

        rows = collect_design_option_rows(doc, view)
        self.grid_options.ItemsSource = rows

        if not rows:
            self.tb_status.Text = \
                'This project has no Design Option Sets.'
        else:
            self.tb_status.Text = \
                '{} option(s) across {} option set(s). ' \
                '"Elements In View" counts elements of the active ' \
                'view assigned to each option.'.format(
                    len(rows),
                    len(set(r.OptionSet for r in rows))
                )


if __name__ == '__main__':
    window = ViewDOPanelWindow(XAML_FILE, __revit__)
    window.show(modal=False)

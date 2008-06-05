"""A grid plane component.

"""
# Author: Prabhu Ramachandran <prabhu_r@users.sf.net>
# Copyright (c) 2005-2006, Enthought, Inc.
# License: BSD Style.

# Enthought library imports.
from enthought.traits.api import Instance, Enum, Int
from enthought.traits.ui.api import View, Group, Item
from enthought.tvtk.api import tvtk
from enthought.persistence import state_pickler

# Local imports.
from enthought.mayavi.core.component import Component
from enthought.mayavi.core.common import error
from enthought.mayavi.core.traits import DRange


######################################################################
# `CustomGridPlane` class.
######################################################################
class CustomGridPlane(Component):
    # The version of this class.  Used for persistence.
    __version__ = 0

    # The TVTK object that extracts the grid plane.  This is created
    # dynamically based on the input data type.
    plane = Instance(tvtk.Object)

    # Minimum x value.
    x_min = DRange(default=0, low_name='_x_low', high_name='_x_high',
                   is_float=False,
                   desc='minimum x value of the domain')

    # Maximum x value.
    x_max = DRange(default=10000, low_name='_x_low', high_name='_x_high',
                   is_float=False,
                   desc='maximum x value of the domain')

    # Minimum y value.
    y_min = DRange(default=0, low_name='_y_low', high_name='_y_high',
                   is_float=False,
                   desc='minimum y value of the domain')

    # Maximum y value.
    y_max = DRange(default=10000, low_name='_y_low', high_name='_y_high',
                   is_float=False,
                   desc='maximum y value of the domain')

    # Minimum z value.
    z_min = DRange(default=0, low_name='_z_low', high_name='_z_high',
                   is_float=False,
                   desc='minimum z value of the domain')

    # Maximum z value.
    z_max = DRange(default=10000, low_name='_z_low', high_name='_z_high',
                   is_float=False,
                   desc='maximum z value of the domain')

    
    ########################################
    # Private traits.

    # Determines the lower/upper limit of the axes for the sliders.
    _x_low = Int(0)
    _x_high = Int(10000)
    _y_low = Int(0)
    _y_high = Int(10000)
    _z_low = Int(0)
    _z_high = Int(10000)

    ########################################
    # View related traits.
    
    # The View for this object.
    view = View(Group(Item(name='x_min'),
                      Item(name='x_max'),
                      Item(name='y_min'),
                      Item(name='y_max'),
                      Item(name='z_min'),
                      Item(name='z_max'),
                      ),
                      resizable=True
                )

    ######################################################################
    # `object` interface
    ######################################################################
    def __get_pure_state__(self):
        d = super(GridPlane, self).__get_pure_state__()
        # These traits are dynamically created.
        for axis in ('x', 'y', 'z'):
            for name in ('_min', '_max'):
                d.pop(axis + name, None)
            d.pop('_' + axis + '_low', None)
            d.pop('_' + axis + '_high', None)

        d.pop('plane', None)
        
        return d

    ######################################################################
    # `Component` interface
    ######################################################################
    def update_pipeline(self):
        """Override this method so that it *updates* the tvtk pipeline
        when data upstream is known to have changed.

        This method is invoked (automatically) when the input fires a
        `pipeline_changed` event.
        """
        if len(self.inputs) == 0:
            return
        input = self.inputs[0].outputs[0]
        plane = None
        if input.is_a('vtkStructuredGrid'):
            plane = tvtk.StructuredGridGeometryFilter()
        elif input.is_a('vtkStructuredPoints') or input.is_a('vtkImageData'):
            plane = tvtk.ImageDataGeometryFilter ()
        elif input.is_a('vtkRectilinearGrid'):
            plane = tvtk.RectilinearGridGeometryFilter ()
        else:
            msg = "The GridPlane component does not support the %s dataset."\
                  %(input.class_name)
            error(msg)
            raise TypeError, msg

        plane.input = input
        self.plane = plane
        self._update_limits()
        self._update_voi()
        self.outputs = [plane.output]

    def update_data(self):
        """Override this method to do what is necessary when upstream
        data changes.

        This method is invoked (automatically) when any of the inputs
        sends a `data_changed` event.
        """
        self._update_limits()
        self._update_voi()
        # Propagate the data_changed event.
        self.data_changed = True

    ######################################################################
    # Non-public methods.
    ######################################################################
    def _update_limits(self):
        extents = self.plane.input.whole_extent
        self._x_low, self._x_high = extents[:2]
        self._y_low, self._y_high = extents[2:4]
        self._z_low, self._z_high = extents[4:]
        
    def _x_min_changed(self, val):
        if val > self.x_max:
            self.x_max = val
        else:
            self._update_voi()

    def _x_max_changed(self, val):
        if val < self.x_min:
            self.x_min = val
        else:
            self._update_voi()

    def _y_min_changed(self, val):
        if val > self.y_max:
            self.y_max = val
        else:
            self._update_voi()

    def _y_max_changed(self, val):
        if val < self.y_min:
            self.y_min = val
        else:
            self._update_voi()

    def _z_min_changed(self, val):
        if val > self.z_max:
            self.z_max = val
        else:
            self._update_voi()

    def _z_max_changed(self, val):
        if val < self.z_min:
            self.z_min = val
        else:
            self._update_voi()

    def _update_voi(self):
        if len(self.inputs) == 0:
            return
        plane = self.plane
        extents = (self.x_min, self.x_max,
                   self.y_min, self.y_max,
                   self.z_min, self.z_max)
        try:
            plane.set_extent(extents)
        except AttributeError:
            plane.extent = tuple(extents)

        plane.update_whole_extent()
        plane.update()
        self.data_changed = True

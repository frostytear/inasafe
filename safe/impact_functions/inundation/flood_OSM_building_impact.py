from safe.impact_functions.core import FunctionProvider
from safe.impact_functions.core import get_hazard_layer, get_exposure_layer
from safe.impact_functions.core import get_question
from safe.storage.vector import Vector
from safe.common.utilities import ugettext as _
from safe.common.tables import Table, TableRow
from safe.common.dynamic_translations import names as internationalised_values
from safe.engine.interpolation import assign_hazard_values_to_exposure_data


class FloodBuildingImpactFunction(FunctionProvider):
    """Inundation impact on building data

    :author Ole Nielsen, Kristy van Putten
    # this rating below is only for testing a function, not the real one
    :rating 0
    :param requires category=='hazard' and \
                    subcategory in ['flood', 'tsunami']

    :param requires category=='exposure' and \
                    subcategory=='structure' and \
                    layertype=='vector'
    """

    # Function documentation
    target_field = 'INUNDATED'
    title = _('Be temporarily closed')
    synopsis = _('To assess the impacts of inundation on building footprints\
        originating from OpenStreetMap (OSM).')
    actions = _('Provide details about where critical response areas are')
    # citations must be a list
    citations = _('Hutchings, Field & Parks. Assessment of Flood impacts on\
        buildings. Impact. Vol 66(2). 2012')
    detailed_desc = _('This is an area for free form text where a detailed\
        description of the methodology used is given.')
    permissible_haz_input = _('A raster layer where each cell represents flood\
        dept, or a vector polygon layer where each polygon represents an\
        inundated area. Optionally the user may nominate an attribute in the\
        polygon layer that represents inundation depth.')
    permissible_exp_input = _('vector polygon layer extracted from OSM where\
        each polygon represents the footprint of a building.')
    limitation = _('Lorem ipsum limitation')

    def run(self, layers):
        """Flood impact to buildings (e.g. from Open Street Map)
        """

        threshold = 1.0  # Flood threshold [m]

        # Extract data
        H = get_hazard_layer(layers)    # Depth
        E = get_exposure_layer(layers)  # Building locations

        question = get_question(H.get_name(),
                                E.get_name(),
                                self)

        # Determine attribute name for hazard levels
        if H.is_raster:
            hazard_attribute = 'depth'
        else:
            hazard_attribute = 'FLOODPRONE'

        # Interpolate hazard level to building locations
        I = assign_hazard_values_to_exposure_data(H, E,
                                             attribute_name=hazard_attribute)

        # Extract relevant exposure data
        attribute_names = I.get_attribute_names()
        attributes = I.get_data()
        N = len(I)

        # Calculate building impact
        count = 0
        buildings = {}
        affected_buildings = {}
        for i in range(N):
            if hazard_attribute == 'depth':
                # Get the interpolated depth
                x = float(attributes[i]['depth'])
                x = x > threshold
            elif hazard_attribute == 'FLOODPRONE':
                # Use interpolated polygon attribute
                atts = attributes[i]

                if 'FLOODPRONE' in atts:
                    res = atts['FLOODPRONE']
                    if res is None:
                        x = False
                    else:
                        x = res.lower() == 'yes'
                else:
                    # If there isn't a flood prone attribute,
                    # assume that building is wet if inside polygon
                    # as flag by generic attribute AFFECTED
                    res = atts['Affected']
                    if res is None:
                        x = False
                    else:
                        x = res
            else:
                msg = (_('Unknown hazard type %s. '
                         'Must be either "depth" or "floodprone"')
                       % hazard_attribute)
                raise Exception(msg)

            # Count affected buildings by usage type if available
            if 'type' in attribute_names:
                usage = attributes[i]['type']
            else:
                usage = None

            if usage is not None and usage != 0:
                key = usage
            else:
                key = 'unknown'

            if key not in buildings:
                buildings[key] = 0
                affected_buildings[key] = 0

            # Count all buildings by type
            buildings[key] += 1
            if x is True:
                # Count affected buildings by type
                affected_buildings[key] += 1

                # Count total affected buildings
                count += 1

            # Add calculated impact to existing attributes
            attributes[i][self.target_field] = x

        # Lump small entries and 'unknown' into 'other' category
        for usage in buildings.keys():
            x = buildings[usage]
            if x < 25 or usage == 'unknown':
                if 'other' not in buildings:
                    buildings['other'] = 0
                    affected_buildings['other'] = 0

                buildings['other'] += x
                affected_buildings['other'] += affected_buildings[usage]
                del buildings[usage]
                del affected_buildings[usage]

        # Generate csv file of results
##        fid = open('C:\dki_table_%s.csv' % H.get_name(), 'wb')
##        fid.write('%s, %s, %s\n' % (_('Building type'),
##                                    _('Temporarily closed'),
##                                    _('Total')))
##        fid.write('%s, %i, %i\n' % (_('All'), count, N))

        # Generate simple impact report
        table_body = [question,
                      TableRow([_('Building type'),
                                _('Temporarily closed'),
                                _('Total')],
                               header=True),
                      TableRow([_('All'), count, N])]

##        fid.write('%s, %s, %s\n' % (_('Building type'),
##                                    _('Temporarily closed'),
##                                    _('Total')))

        school_closed = 0
        hospital_closed = 0
        # Generate break down by building usage type is available
        if 'type' in attribute_names:
            # Make list of building types
            building_list = []
            for usage in buildings:

                building_type = usage.replace('_', ' ')

                # Lookup internationalised value if available
                if building_type in internationalised_values:
                    building_type = internationalised_values[building_type]
                else:
                    print ('WARNING: %s could not be translated'
                           % building_type)

                building_list.append([building_type.capitalize(),
                                      affected_buildings[usage],
                                      buildings[usage]])
                if building_type == 'school':
                    school_closed = affected_buildings[usage]
                if building_type == 'hospital':
                    hospital_closed = affected_buildings[usage]
##                fid.write('%s, %i, %i\n' % (building_type.capitalize(),
##                                            affected_buildings[usage],
##                                            buildings[usage]))

            # Sort alphabetically
            building_list.sort()

            #table_body.append(TableRow([_('Building type'),
            #                            _('Temporarily closed'),
            #                            _('Total')], header=True))
            table_body.append(TableRow(_('Breakdown by building type'),
                                       header=True))
            for row in building_list:
                s = TableRow(row)
                table_body.append(s)

##        fid.close()
        table_body.append(TableRow(_('Action Checklist:'), header=True))
        table_body.append(TableRow(_('Are the critical facilities still '
                                     'open?')))
        table_body.append(TableRow(_('Which structures have warning capacity '
                                     '(eg. sirens, speakers, etc.)?')))
        table_body.append(TableRow(_('Which buildings will be evacuation '
                                     'centres?')))
        table_body.append(TableRow(_('Where will we locate the operations '
                                     'centre?')))
        table_body.append(TableRow(_('Where will we locate warehouse and/or '
                                     'distribution centres?')))
        if school_closed > 0:
            table_body.append(TableRow(_('Where will the students from the %d '
                                         'closed schools go to study?') %
                                         school_closed))
        if hospital_closed > 0:
            table_body.append(TableRow(_('Where will the patients from the %d '
                                         'closed hospitals go for treatment '
                                         'and how will we transport them?') %
                                         hospital_closed))

        table_body.append(TableRow(_('Notes'), header=True))
        assumption = _('Buildings are said to be flooded when ')
        if hazard_attribute == 'depth':
            assumption += _('flood levels exceed %.1f m') % threshold
        else:
            assumption += _('in areas marked as flood prone')
        table_body.append(assumption)

        impact_summary = Table(table_body).toNewlineFreeString()
        impact_table = impact_summary
        map_title = _('Buildings inundated')

        # Create style
        style_classes = [dict(label=_('Not Flooded'), min=0, max=0,
                              colour='#1EFC7C', transparency=0, size=1),
                         dict(label=_('Flooded'), min=1, max=1,
                              colour='#F31A1C', transparency=0, size=1)]
        style_info = dict(target_field=self.target_field,
                          style_classes=style_classes)

        # Create vector layer and return
        V = Vector(data=attributes,
                   projection=I.get_projection(),
                   geometry=I.get_geometry(),
                   name=_('Estimated buildings affected'),
                   keywords={'impact_summary': impact_summary,
                             'impact_table': impact_table,
                             'map_title': map_title
                             },
                   style_info=style_info)
        return V

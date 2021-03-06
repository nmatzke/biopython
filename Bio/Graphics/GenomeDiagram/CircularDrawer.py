# Copyright 2003-2008 by Leighton Pritchard.  All rights reserved.
# Revisions copyright 2008-2009 by Peter Cock.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
#
# Contact:       Leighton Pritchard, Scottish Crop Research Institute,
#                Invergowrie, Dundee, Scotland, DD2 5DA, UK
#                L.Pritchard@scri.ac.uk
################################################################################

""" CircularDrawer module

    Provides:

    o CircularDrawer -  Drawing object for circular diagrams

    For drawing capabilities, this module uses reportlab to draw and write
    the diagram:

    http://www.reportlab.com

    For dealing with biological information, the package expects BioPython
    objects:

    http://www.biopython.org
"""

# ReportLab imports
from reportlab.graphics.shapes import *
from reportlab.lib import colors
from reportlab.pdfbase import _fontdata
from reportlab.graphics.shapes import ArcPath

# GenomeDiagram imports
from AbstractDrawer import AbstractDrawer, draw_polygon, intermediate_points
from FeatureSet import FeatureSet
from GraphSet import GraphSet

from math import ceil, pi, cos, sin, asin
from string import join

class CircularDrawer(AbstractDrawer):
    """ CircularDrawer(AbstractDrawer)

        Inherits from:

        o AbstractDrawer

        Provides:

        Methods:

        o __init__(self, parent=None, pagesize='A3', orientation='landscape',
                 x=0.05, y=0.05, xl=None, xr=None, yt=None, yb=None,
                 start=None, end=None, tracklines=0, track_size=0.75,
                 circular=1) Called on instantiation

        o set_page_size(self, pagesize, orientation)    Set the page size to the
                                                    passed size and orientation

        o set_margins(self, x, y, xl, xr, yt, yb)   Set the drawable area of the
                                                    page

        o set_bounds(self, start, end)  Set the bounds for the elements to be
                                        drawn

        o is_in_bounds(self, value)     Returns a boolean for whether the position
                                        is actually to be drawn

        o __len__(self)     Returns the length of sequence that will be drawn


        o draw(self)    Place the drawing elements on the diagram

        o init_fragments(self)  Calculate information
                                about sequence fragment locations on the drawing

        o set_track_heights(self)   Calculate information about the offset of
                                    each track from the fragment base
                                    
        o draw_test_tracks(self)    Add lines demarcating each track to the
                                    drawing

        o draw_track(self, track)   Return the contents of the passed track as
                                    drawing elements

        o draw_scale(self, track)   Return a scale for the passed track as
                                    drawing elements

        o draw_greytrack(self, track)   Return a grey background and superposed
                                        label for the passed track as drawing
                                        elements

        o draw_feature_set(self, set)   Return the features in the passed set as
                                        drawing elements

        o draw_feature(self, feature)   Return a single feature as drawing
                                        elements

        o get_feature_sigil(self, feature, x0, x1, fragment)    Return a single
                                        feature as its sigil in drawing elements

        o draw_graph_set(self, set)     Return the data in a set of graphs as
                                        drawing elements

        o draw_line_graph(self, graph)  Return the data in a graph as a line
                                        graph in drawing elements

        o draw_heat_graph(self, graph)  Return the data in a graph as a heat
                                        graph in drawing elements

        o draw_bar_graph(self, graph)   Return the data in a graph as a bar
                                        graph in drawing elements

        o canvas_angle(self, base)      Return the angle, and cos and sin of
                                        that angle, subtended by the passed
                                        base position at the diagram center

        o draw_arc(self, inner_radius, outer_radius, startangle, endangle,
                    color)    Return a drawable element describing an arc

        Attributes:

        o tracklines    Boolean for whether to draw lines dilineating tracks

        o pagesize      Tuple describing the size of the page in pixels

        o x0            Float X co-ord for leftmost point of drawable area

        o xlim          Float X co-ord for rightmost point of drawable area

        o y0            Float Y co-ord for lowest point of drawable area

        o ylim          Float Y co-ord for topmost point of drawable area

        o pagewidth     Float pixel width of drawable area

        o pageheight    Float pixel height of drawable area

        o xcenter       Float X co-ord of center of drawable area

        o ycenter       Float Y co-ord of center of drawable area

        o start         Int, base to start drawing from

        o end           Int, base to stop drawing at

        o length        Size of sequence to be drawn

        o track_size    Float (0->1) the proportion of the track height to
                        draw in

        o drawing       Drawing canvas

        o drawn_tracks  List of ints denoting which tracks are to be drawn

        o current_track_level   Int denoting which track is currently being
                                drawn

        o track_offsets     Dictionary of number of pixels that each track top,
                            center and bottom is offset from the base of a
                            fragment, keyed by track

        o sweep     Float (0->1) the proportion of the circle circumference to
                    use for the diagram

    """
    def __init__(self, parent=None, pagesize='A3', orientation='landscape',
                 x=0.05, y=0.05, xl=None, xr=None, yt=None, yb=None,
                 start=None, end=None, tracklines=0, track_size=0.75,
                 circular=1):
        """ __init__(self, parent, pagesize='A3', orientation='landscape',
                     x=0.05, y=0.05, xl=None, xr=None, yt=None, yb=None,
                     start=None, end=None, tracklines=0, track_size=0.75,
                     circular=1)

            o parent    Diagram object containing the data that the drawer
                        draws

            o pagesize  String describing the ISO size of the image, or a tuple
                        of pixels

            o orientation   String describing the required orientation of the
                            final drawing ('landscape' or 'portrait')

            o x         Float (0->1) describing the relative size of the X
                        margins to the page

            o y         Float (0->1) describing the relative size of the Y
                        margins to the page

            o xl        Float (0->1) describing the relative size of the left X
                        margin to the page (overrides x)

            o xl        Float (0->1) describing the relative size of the left X
                        margin to the page (overrides x)

            o xr        Float (0->1) describing the relative size of the right X
                        margin to the page (overrides x)

            o yt        Float (0->1) describing the relative size of the top Y
                        margin to the page (overrides y)

            o yb        Float (0->1) describing the relative size of the lower Y
                        margin to the page (overrides y)

            o start     Int, the position to begin drawing the diagram at

            o end       Int, the position to stop drawing the diagram at

            o tracklines    Boolean flag to show (or not) lines delineating tracks
                            on the diagram            
                            
            o track_size    The proportion of the available track height that
                            should be taken up in drawing

            o circular      Boolean flaw to show whether the passed sequence is
                            circular or not
        """
        # Use the superclass' instantiation method
        AbstractDrawer.__init__(self, parent, pagesize, orientation,
                                  x, y, xl, xr, yt, yb, start, end,
                                  tracklines)

        # Useful measurements on the page
        self.track_size = track_size
        if circular == False:   # Determine the proportion of the circumference
            self.sweep = 0.9    # around which information will be drawn
        else:
            self.sweep = 1


    def set_track_heights(self):
        """ set_track_heights(self)

            Since tracks may not be of identical heights, the bottom and top
            radius for each track is stored in a dictionary - self.track_radii,
            keyed by track number
        """
        top_track = max(self.drawn_tracks)     # The 'highest' track to draw

        trackunit_sum = 0           # Holds total number of 'units' taken up by all tracks
        trackunits = {}             # Holds start and end units for each track keyed by track number
        heightholder = 0            # placeholder variable
        for track in range(1, top_track+1):    # track numbers to 'draw'
            try:
                trackheight = self._parent[track].height    # Get track height
            except:
                trackheight = 1                             # ...or default to 1
            trackunit_sum += trackheight    # increment total track unit height
            trackunits[track] = (heightholder, heightholder+trackheight)
            heightholder += trackheight     # move to next height
        trackunit_height = 0.5*min(self.pagewidth, self.pageheight)/trackunit_sum

        # Calculate top and bottom radii for each track
        self.track_radii = {}      # The inner, outer and center radii for each track
        track_crop = trackunit_height*(1-self.track_size)/2.    # 'step back' in pixels
        for track in trackunits:
            top = trackunits[track][1]*trackunit_height-track_crop
            btm = trackunits[track][0]*trackunit_height+track_crop
            ctr = btm+(top-btm)/2.
            self.track_radii[track] = (btm, ctr, top)

    def draw(self):
        """ draw(self)

            Draw a circular diagram of the stored data
        """
        # Instantiate the drawing canvas
        self.drawing = Drawing(self.pagesize[0], self.pagesize[1])

        feature_elements = []           # holds feature elements
        feature_labels = []             # holds feature labels
        greytrack_bgs = []              # holds track background
        greytrack_labels = []           # holds track foreground labels
        scale_axes = []                 # holds scale axes
        scale_labels = []               # holds scale axis labels

        # Get tracks to be drawn and set track sizes
        self.drawn_tracks = self._parent.get_drawn_levels()        
        self.set_track_heights()

        # Go through each track in the parent (if it is to be drawn) one by
        # one and collate the data as drawing elements
        for track_level in self._parent.get_drawn_levels():
            self.current_track_level = track_level
            track = self._parent[track_level]
            gbgs, glabels = self.draw_greytrack(track)    # Greytracks
            greytrack_bgs.append(gbgs)
            greytrack_labels.append(glabels)
            features, flabels = self.draw_track(track)   # Features and graphs
            feature_elements.append(features)
            feature_labels.append(flabels)
            if track.scale:
                axes, slabels = self.draw_scale(track)       # Scale axes
                scale_axes.append(axes)
                scale_labels.append(slabels)

        # Groups listed in order of addition to page (from back to front)
        # Draw track backgrounds
        # Draw features and graphs
        # Draw scale axes
        # Draw scale labels
        # Draw feature labels
        # Draw track labels
        element_groups = [greytrack_bgs, feature_elements,
                          scale_axes, scale_labels,
                          feature_labels, greytrack_labels
                          ]
        for element_group in element_groups:
            for element_list in element_group:
                [self.drawing.add(element) for element in element_list]
            
        if self.tracklines:             # Draw test tracks over top of diagram
            self.draw_test_tracks()


    def draw_track(self, track):
        """ draw_track(self, track) -> ([element, element,...], [element, element,...])

            o track     Track object

            Return tuple of (list of track elements, list of track labels)           
        """
        track_elements = [] # Holds elements for features and graphs
        track_labels = []   # Holds labels for features and graphs
        
        # Distribution dictionary for dealing with different set types
        set_methods = {FeatureSet: self.draw_feature_set,
                       GraphSet: self.draw_graph_set
                       }
        
        for set in track.get_sets():        # Draw the feature or graph sets
            elements, labels = set_methods[set.__class__](set)
            track_elements += elements
            track_labels += labels
        return track_elements, track_labels


    def draw_feature_set(self, set):
        """ draw_feature_set(self, set) -> ([element, element,...], [element, element,...])

            o set       FeatureSet object

            Returns a tuple (list of elements describing features, list of
            labels for elements)
        """
        #print 'draw feature set'
        feature_elements = []   # Holds diagram elements belonging to the features
        label_elements = []     # Holds diagram elements belonging to feature labels 

        # Collect all the elements for the feature set
        for feature in set.get_features():
            if self.is_in_bounds(feature.start) or self.is_in_bounds(feature.end):
                features, labels = self.draw_feature(feature)
                feature_elements += features
                label_elements += labels

        return feature_elements, label_elements
        

    def draw_feature(self, feature):
        """ draw_feature(self, feature, parent_feature=None) -> ([element, element,...], [element, element,...])

            o feature           Feature containing location info

            Returns tuple of (list of elements describing single feature, list
            of labels for those elements)
        """        
        feature_elements = []   # Holds drawable elements for a single feature
        label_elements = []     # Holds labels for a single feature

        if feature.hide:    # Don't show feature: return early
            return feature_elements, label_elements

        # A single feature may be split into subfeatures, so loop over them
        for locstart, locend in feature.locations:
            # Get sigil for the feature/ each subfeature
            feature_sigil, label = self.get_feature_sigil(feature, locstart, locend)
            feature_elements.append(feature_sigil)
            if label is not None:   # If there's a label
                label_elements.append(label)

        return feature_elements, label_elements


    def get_feature_sigil(self, feature, locstart, locend):
        """ get_feature_sigil(self, feature, x0, x1, fragment) -> (element, element)

            o feature       Feature object

            o locstart      The start position of the feature

            o locend        The end position of the feature

            Returns a drawable indicator of the feature, and any required label
            for it
        """
        # Establish the co-ordinates for the sigil
        btm, ctr, top = self.track_radii[self.current_track_level]
        startangle, startcos, startsin = self.canvas_angle(locstart)
        endangle, endcos, endsin = self.canvas_angle(locend)
        midangle, midcos, midsin = self.canvas_angle(locend+locstart/2)

        # Distribution dictionary for various ways of drawing the feature
        # Each method takes the inner and outer radii, the start and end angle
        # subtended at the diagram center, and the color as arguments
        draw_methods = {'BOX': self._draw_arc,
                        'ARROW': self._draw_arc_arrow,
                        }
                        
        # Get sigil for the feature, location dependent on the feature strand        
        method = draw_methods[feature.sigil]
        if feature.color == colors.white:
            border = colors.black
        else:
            border = feature.color
        if feature.strand == 0:
            sigil = method(btm, top, startangle, endangle, feature.color,
                           border)
        if feature.strand == 1:
            sigil = method(ctr, top, startangle, endangle, feature.color,
                           border, orientation='right')
        if feature.strand == -1:
            sigil = method(btm, ctr, startangle, endangle, feature.color,
                           border, orientation='left')
        if feature.label:   # Feature needs a label
            label = String(0, 0, feature.name.strip(),
                           fontName=feature.label_font,
                           fontSize=feature.label_size,
                           fillColor=feature.label_color)
            labelgroup = Group(label)
            label_angle = startangle + 0.5 * pi     # Make text radial
            sinval, cosval = startsin, startcos
            if feature.strand == 1:    # Feature is on top, or covers both strands
                if startangle < pi: # Turn text round and anchor end to inner radius
                    sinval, cosval = endsin, endcos
                    label_angle = endangle - 0.5 * pi
                    labelgroup.contents[0].textAnchor = 'end'
                pos = self.xcenter+top*sinval
                coslabel = cos(label_angle)
                sinlabel = sin(label_angle)    
                labelgroup.transform = (coslabel,-sinlabel,sinlabel,coslabel,
                                        pos, self.ycenter+top*cosval)
            elif feature.strand == -1:                           # Feature on bottom strand
                if startangle > pi: # Anchor end to inner radius
                    labelgroup.contents[0].textAnchor='end'
                else:               # Turn text round
                    sinval, cosval = endsin, endcos
                    label_angle += pi
                pos = self.xcenter+btm*sinval
                coslabel = cos(label_angle)
                sinlabel = sin(label_angle)
                #labelgroup.transform = (coslabel,-sinlabel,sinlabel,coslabel,
                #                        pos, self.ycenter+btm*cosval)
                labelgroup.transform = (coslabel,-sinlabel,sinlabel,coslabel,
                                        pos, self.ycenter+btm*cosval)
            else:   # feature.strand == 0
                if startangle > pi: # Anchor end to inner radius
                    labelgroup.contents[0].textAnchor='end'
                    sinval, cosval = endsin, endcos
                else:               # Turn text round
                    label_angle += pi
                pos = self.xcenter+btm*sinval
                coslabel = cos(label_angle)
                sinlabel = sin(label_angle)
                labelgroup.transform = (coslabel,-sinlabel,sinlabel,coslabel,
                                        pos, self.ycenter+btm*cosval)
        else:
            labelgroup = None
        #if locstart > locend:
        #    print locstart, locend, feature.strand, sigil, feature.name
        #print locstart, locend, feature.name
        return sigil, labelgroup



    def draw_graph_set(self, set):
        """ draw_graph_set(self, set) -> ([element, element,...], [element, element,...])
        
            o set       GraphSet object

            Returns tuple (list of graph elements, list of graph labels)
        """
        #print 'draw graph set'
        elements = []   # Holds graph elements

        # Distribution dictionary for how to draw the graph
        style_methods = {'line': self.draw_line_graph,
                         'heat': self.draw_heat_graph,
                         'bar': self.draw_bar_graph
                         }

        for graph in set.get_graphs():
            #print graph.name
            elements += style_methods[graph.style](graph)

        return elements, []


    def draw_line_graph(self, graph):
        """ draw_line_graph(self, graph, center) -> [element, element,...]

            o graph     GraphData object

            Returns a line graph as a list of drawable elements
        """
        #print '\tdraw_line_graph'
        line_elements = []  # holds drawable elements

        # Get graph data
        data_quartiles = graph.quartiles()
        minval, maxval = data_quartiles[0],data_quartiles[4]
        btm, ctr, top = self.track_radii[self.current_track_level]
        trackheight = 0.5*(top-btm)
        datarange = maxval - minval
        if datarange == 0:
            datarange = trackheight
        data = graph[self.start:self.end]

        # midval is the value at which the x-axis is plotted, and is the
        # central ring in the track
        if graph.center is None:
            midval = (maxval + minval)/2.    
        else:
            midval = graph.center
        # Whichever is the greatest difference: max-midval or min-midval, is
        # taken to specify the number of pixel units resolved along the
        # y-axis
        resolution = max((midval-minval), (maxval-midval))

        # Start from first data point
        pos, val = data[0]
        lastangle, lastcos, lastsin = self.canvas_angle(pos)
        # We calculate the track height
        posheight = trackheight*(val-midval)/resolution + ctr
        lastx = self.xcenter+posheight*lastsin  # start xy coords
        lasty = self.ycenter+posheight*lastcos
        for pos, val in data:
            posangle, poscos, possin = self.canvas_angle(pos)
            posheight = trackheight*(val-midval)/resolution + ctr
            x = self.xcenter+posheight*possin   # next xy coords
            y = self.ycenter+posheight*poscos
            line_elements.append(Line(lastx, lasty, x, y,
                                      strokeColor = graph.poscolor,
                                      strokeWidth = graph.linewidth))
            lastx, lasty, = x, y
        return line_elements
        

    def draw_bar_graph(self, graph):
        """ draw_bar_graph(self, graph) -> [element, element,...]

            o graph     Graph object

            Returns a list of drawable elements for a bar graph of the passed
            Graph object
        """
        #print '\tdraw_bar_graph'
        # At each point contained in the graph data, we draw a vertical bar
        # from the track center to the height of the datapoint value (positive
        # values go up in one color, negative go down in the alternative
        # color).
        bar_elements = []
        
        # Set the number of pixels per unit for the data
        data_quartiles = graph.quartiles()
        minval, maxval = data_quartiles[0],data_quartiles[4]
        btm, ctr, top = self.track_radii[self.current_track_level]
        trackheight = 0.5*(top-btm)
        datarange = maxval - minval
        if datarange == 0:
            datarange = trackheight
        data = graph[self.start:self.end]
        # midval is the value at which the x-axis is plotted, and is the
        # central ring in the track
        if graph.center is None:
            midval = (maxval + minval)/2.    
        else:
            midval = graph.center

        # Convert data into 'binned' blocks, covering half the distance to the
        # next data point on either side, accounting for the ends of fragments
        # and tracks
        newdata = intermediate_points(self.start, self.end,
                                      graph[self.start:self.end])

        # Whichever is the greatest difference: max-midval or min-midval, is
        # taken to specify the number of pixel units resolved along the
        # y-axis
        resolution = max((midval-minval), (maxval-midval))
        if resolution == 0:
            resolution = trackheight

        # Create elements for the bar graph based on newdata
        for pos0, pos1, val in newdata:
            pos0angle, pos0cos, pos0sin = self.canvas_angle(pos0)
            pos1angle, pos1cos, pos1sin = self.canvas_angle(pos1)

            barval = trackheight*(val-midval)/resolution
            if barval >=0:
                barcolor = graph.poscolor
            else:
                barcolor = graph.negcolor

            # Draw bar
            bar_elements.append(self._draw_arc(ctr, ctr+barval, pos0angle,
                                              pos1angle, barcolor))
        return bar_elements

    


    def draw_heat_graph(self, graph):
        """ draw_heat_graph(self, graph) -> [element, element,...]

            o graph     Graph object

            Returns a list of drawable elements for the heat graph
        """
        #print '\tdraw_heat_graph'
        # At each point contained in the graph data, we draw a box that is the
        # full height of the track, extending from the midpoint between the
        # previous and current data points to the midpoint between the current
        # and next data points
        heat_elements = []      # holds drawable elements

        # Get graph data
        data_quartiles = graph.quartiles()
        minval, maxval = data_quartiles[0],data_quartiles[4]
        midval = (maxval + minval)/2.    # mid is the value at the X-axis
        btm, ctr, top = self.track_radii[self.current_track_level]
        trackheight = (top-btm)
        newdata = intermediate_points(self.start, self.end,
                                      graph[self.start:self.end])

        # Create elements on the graph, indicating a large positive value by
        # the graph's poscolor, and a large negative value by the graph's
        # negcolor attributes
        for pos0, pos1, val in newdata:
            pos0angle, pos0cos, pos0sin = self.canvas_angle(pos0)
            pos1angle, pos1cos, pos1sin = self.canvas_angle(pos1)

            # Calculate the heat color, based on the differential between
            # the value and the median value
            heat = colors.linearlyInterpolatedColor(graph.poscolor,
                                                    graph.negcolor,
                                                    maxval, minval, val)
            
            # Draw heat box
            heat_elements.append(self._draw_arc(btm, top, pos0angle, pos1angle,
                                               heat, border=heat))
        return heat_elements


    def draw_scale(self, track):
        """ draw_scale(self, track) -> ([element, element,...], [element, element,...])

            o track     Track object

            Returns a tuple of (list of elements in the scale, list of labels
            in the scale)
        """
        scale_elements = []     # holds axes and ticks
        scale_labels = []       # holds labels

        if not track.scale:     # no scale required, exit early
            return [], []

        # Get track locations
        btm, ctr, top = self.track_radii[self.current_track_level]
        trackheight = (top-ctr)
        
        # X-axis
        if self.sweep < 1 :
            #Draw an arc, leaving out the wedge
            p = ArcPath(strokeColor=track.scale_color, fillColor=None)
            #Note reportlab counts angles anti-clockwise from the horizontal
            #(as in mathematics, e.g. complex numbers and polar coordinates)
            #in degrees.
            p.addArc(self.xcenter, self.ycenter, ctr,
                     startangledegrees=90-360*self.sweep,
                     endangledegrees=90)
            scale_elements.append(p)
            del p
        else :
            #Draw a full circle
            scale_elements.append(Circle(self.xcenter, self.ycenter, ctr,
                                         strokeColor=track.scale_color,
                                         fillColor=None))

        if track.scale_ticks:   # Ticks are required on the scale
            # Draw large ticks 
            #I want the ticks to be consistently positioned relative to
            #the start of the sequence (position 0), not relative to the
            #current viewpoint (self.start and self.end)

            ticklen = track.scale_largeticks * trackheight
            tickiterval = int(track.scale_largetick_interval)
            #Note that we could just start the list of ticks using
            #range(0,self.end,tickinterval) and the filter out the
            #ones before self.start - but this seems wasteful.
            #Using tickiterval * (self.start/tickiterval) is a shortcut.
            largeticks = [pos for pos \
                          in range(tickiterval * (self.start/tickiterval),
                                   int(self.end),
                                   tickiterval) \
                          if pos >= self.start]
            for tickpos in largeticks:
                tick, label = self.draw_tick(tickpos, ctr, ticklen,
                                             track,
                                             track.scale_largetick_labels)
                scale_elements.append(tick)
                if label is not None:   # If there's a label, add it
                    scale_labels.append(label)
            # Draw small ticks
            ticklen = track.scale_smallticks * trackheight
            tickiterval = int(track.scale_smalltick_interval)
            smallticks = [pos for pos \
                          in range(tickiterval * (self.start/tickiterval),
                                   int(self.end),
                                   tickiterval) \
                          if pos >= self.start]
            for tickpos in smallticks:
                tick, label = self.draw_tick(tickpos, ctr, ticklen,
                                             track,
                                             track.scale_smalltick_labels)
                scale_elements.append(tick)
                if label is not None:   # If there's a label, add it
                    scale_labels.append(label)
        
        # Check to see if the track contains a graph - if it does, get the
        # minimum and maximum values, and put them on the scale Y-axis
        # at 60 degree intervals, ordering the labels by graph_id
        if track.axis_labels:
            for set in track.get_sets():
                if set.__class__ is GraphSet:
                    # Y-axis
                    for n in xrange(7):
                        angle = n * 1.0471975511965976
                        ticksin, tickcos = sin(angle), cos(angle)
                        x0, y0 = self.xcenter+btm*ticksin, self.ycenter+btm*tickcos
                        x1, y1 = self.xcenter+top*ticksin, self.ycenter+top*tickcos
                        scale_elements.append(Line(x0, y0, x1, y1,
                                                   strokeColor=track.scale_color))

                        graph_label_min = []
                        graph_label_max = []
                        graph_label_mid = []
                        for graph in set.get_graphs():                        
                            quartiles = graph.quartiles()
                            minval, maxval = quartiles[0], quartiles[4]
                            if graph.center is None:
                                midval = (maxval + minval)/2.
                                graph_label_min.append("%.3f" % minval)
                                graph_label_max.append("%.3f" % maxval)
                                graph_label_mid.append("%.3f" % midval)
                            else:
                                diff = max((graph.center-minval),
                                           (maxval-graph.center))
                                minval = graph.center-diff
                                maxval = graph.center+diff
                                midval = graph.center
                                graph_label_mid.append("%.3f" % midval)
                                graph_label_min.append("%.3f" % minval)
                                graph_label_max.append("%.3f" % maxval)
                        xmid, ymid = (x0+x1)/2., (y0+y1)/2.
                        for limit, x, y, in [(graph_label_min, x0, y0),
                                             (graph_label_max, x1, y1),
                                             (graph_label_mid, xmid, ymid)]:
                            label = String(0, 0, join(limit, ';'),
                                           fontName=track.scale_font,
                                           fontSize=track.scale_fontsize,
                                           fillColor=track.scale_color)
                            label.textAnchor = 'middle'
                            labelgroup = Group(label)
                            labelgroup.transform = (tickcos, -ticksin,
                                                    ticksin, tickcos,
                                                    x, y)
                            scale_labels.append(labelgroup)

        return scale_elements, scale_labels


    def draw_tick(self, tickpos, ctr, ticklen, track, draw_label):
        """ draw_tick(self, tickpos, ctr, ticklen) -> (element, element)

            o tickpos   Int, position of the tick on the sequence

            o ctr       Float, Y co-ord of the center of the track

            o ticklen   How long to draw the tick

            o track     Track, the track the tick is drawn on

            o draw_label    Boolean, write the tick label?

            Returns a drawing element that is the tick on the scale
        """
        # Calculate tick co-ordinates
        tickangle, tickcos, ticksin = self.canvas_angle(tickpos)
        x0, y0 = self.xcenter+ctr*ticksin, self.ycenter+ctr*tickcos
        x1, y1 = self.xcenter+(ctr+ticklen)*ticksin, self.ycenter+(ctr+ticklen)*tickcos
        # Calculate height of text label so it can be offset on lower half
        # of diagram
        # LP: not used, as not all fonts have ascent_descent data in reportlab.pdfbase._fontdata
        #label_offset = _fontdata.ascent_descent[track.scale_font][0]*\
        #               track.scale_fontsize/1000.
        tick = Line(x0, y0, x1, y1, strokeColor=track.scale_color)
        if draw_label:                          # Put tick position on as label
            if track.scale_format == 'SInt':
                if tickpos >= 1000000:
                    tickstring = str(tickpos/1000000) + " Mbp"
                elif tickpos >= 1000:
                    tickstring = str(tickpos/1000) + " Kbp"
                else:
                    tickstring = str(tickpos)
            else:
                tickstring = str(tickpos)
            label = String(0, 0, tickstring,  # Make label string
                           fontName=track.scale_font,
                           fontSize=track.scale_fontsize,
                           fillColor=track.scale_color)
            if tickangle > pi:
                label.textAnchor = 'end'
            # LP: This label_offset depends on ascent_descent data, which is not available for all 
            # fonts, so has been deprecated.
            #if 0.5*pi < tickangle < 1.5*pi:
            #    y1 -= label_offset
            labelgroup = Group(label)
            labelgroup.transform = (1,0,0,1, x1, y1)
        else:
            labelgroup = None
        return tick, labelgroup


    def draw_test_tracks(self):
        """ draw_test_tracks(self)

            Draw blue ones indicating tracks to be drawn, with a green line
            down the center.
        """
        #print 'drawing test tracks'
        # Add lines only for drawn tracks
        for track in self.drawn_tracks:
            btm, ctr, top = self.track_radii[track]            
            self.drawing.add(Circle(self.xcenter, self.ycenter, top,
                                    strokeColor=colors.blue,
                                    fillColor=None))  # top line
            self.drawing.add(Circle(self.xcenter, self.ycenter, ctr,
                                    strokeColor=colors.green,
                                    fillColor=None))  # middle line
            self.drawing.add(Circle(self.xcenter, self.ycenter, btm,
                                    strokeColor=colors.blue,
                                    fillColor=None))  # bottom line


    def draw_greytrack(self, track):
        """ draw_greytrack(self)

            o track     Track object

            Put in a grey background to the current track, if the track
            specifies that we should
        """
        greytrack_bgs = []      # Holds track backgrounds
        greytrack_labels = []   # Holds track foreground labels

        if not track.greytrack: # No greytrack required, return early
            return [], []

        # Get track location
        btm, ctr, top = self.track_radii[self.current_track_level]

        # Make background
        if self.sweep < 1 :
            #Make a partial circle, a large arc box
            #This method assumes the correct center for us.
            bg = self._draw_arc(btm, top, 0, 2*pi*self.sweep,
                                colors.Color(0.98, 0.98, 0.98))
        else :
            #Make a full circle (using a VERY thick linewidth)
            bg = Circle(self.xcenter, self.ycenter, ctr, 
                        strokeColor = colors.Color(0.98, 0.98, 0.98),
                        fillColor=None, strokeWidth=top-btm)
        greytrack_bgs.append(bg)

        if track.greytrack_labels:  # Labels are required for this track
            labelstep = self.length/track.greytrack_labels  # label interval
            for pos in range(self.start, self.end, int(labelstep)):
                label = String(0, 0, track.name,            # Add a new label at
                           fontName=track.greytrack_font,   # each interval
                           fontSize=track.greytrack_fontsize,
                           fillColor=track.greytrack_fontcolor)
                theta, costheta, sintheta = self.canvas_angle(pos)
                x,y = self.xcenter+btm*sintheta, self.ycenter+btm*costheta  # start text halfway up marker
                labelgroup = Group(label)
                labelangle = self.sweep*2*pi*(pos-self.start)/self.length - pi/2
                if theta > pi:  
                    label.textAnchor = 'end'    # Anchor end of text to inner radius
                    labelangle += pi            # and reorient it
                cosA, sinA = cos(labelangle), sin(labelangle)
                labelgroup.transform = (cosA, -sinA, sinA,
                                        cosA, x, y)
                if not self.length-x <= labelstep:  # Don't overrun the circle
                    greytrack_labels.append(labelgroup)

        return greytrack_bgs, greytrack_labels


    def canvas_angle(self, base):
        """ canvas_angle(self, base) -> (float, float, float)
        """
        angle = self.sweep*2*pi*(base-self.start)/self.length
        return (angle, cos(angle), sin(angle))


    def _draw_arc(self, inner_radius, outer_radius, startangle, endangle,
                 color, border=None, colour=None, **kwargs):
        """ draw_arc(self, inner_radius, outer_radius, startangle, endangle, color)
                -> Group

            o inner_radius  Float distance of inside of arc from drawing center

            o outer_radius  Float distance of outside of arc from drawing center

            o startangle    Float angle subtended by start of arc at drawing center
                            (in radians)

            o endangle      Float angle subtended by end of arc at drawing center
                            (in radians)

            o color        colors.Color object for arc (overridden by backwards
                           compatible argument with UK spelling, colour).

            Returns a closed path object describing an arced box corresponding to
            the passed values.  For very small angles, a simple four sided
            polygon is used.
        """
        #Let the UK spelling (colour) override the USA spelling (color)
        if colour is not None:
            color = colour

        if border is None:
            border = color

        if color is None:
            color = colour
        if color == colors.white and border is None:   # Force black border on 
            strokecolor = colors.black                 # white boxes with
        elif border is None:                           # undefined border, else
            strokecolor = color                        # use fill colour
        elif border is not None:
            strokecolor = border

        angle = float(endangle - startangle)    # angle subtended by arc
        if angle>.01:  # Wide arc, represent with multiple boxes
            p = ArcPath(strokeColor=strokecolor,
                        fillColor=color,
                        strokewidth=0)
            #Note reportlab counts angles anti-clockwise from the horizontal
            #(as in mathematics, e.g. complex numbers and polar coordinates)
            #but we use clockwise from the vertical.  Also reportlab uses
            #degrees, but we use radians.
            p.addArc(self.xcenter, self.ycenter, inner_radius,
                     90 - (endangle * 180 / pi), 90 - (startangle * 180 / pi),
                     moveTo=True)
            p.addArc(self.xcenter, self.ycenter, outer_radius,
                     90 - (endangle * 180 / pi), 90 - (startangle * 180 / pi),
                     reverse=True)
            p.closePath()
            return p
        else :
            #Cheat and just use a four sided polygon.
            # Calculate trig values for angle and coordinates
            startcos, startsin = cos(startangle), sin(startangle)
            endcos, endsin = cos(endangle), sin(endangle)
            x0,y0 = self.xcenter, self.ycenter      # origin of the circle
            x1,y1 = (x0+inner_radius*startsin, y0+inner_radius*startcos)
            x2,y2 = (x0+inner_radius*endsin, y0+inner_radius*endcos)
            x3,y3 = (x0+outer_radius*endsin, y0+outer_radius*endcos)
            x4,y4 = (x0+outer_radius*startsin, y0+outer_radius*startcos)
            return draw_polygon([(x1,y1),(x2,y2),(x3,y3),(x4,y4)], color, border)

    def _draw_arc_arrow(self, inner_radius, outer_radius, startangle, endangle,
                  color, border=None,
                  shaft_height_ratio=0.4, head_length_ratio=1.0, orientation='right',
                  colour=None, **kwargs):
        """Draw an arrow along an arc."""
        #Let the UK spelling (colour) override the USA spelling (color)
        if colour is not None:
            color = colour

        if border is None:
            border = color

        if color is None:
            color = colour
        if color == colors.white and border is None:   # Force black border on 
            strokecolor = colors.black                 # white boxes with
        elif border is None:                           # undefined border, else
            strokecolor = color                        # use fill colour
        elif border is not None:
            strokecolor = border

        #if orientation == 'right':
        #    startangle, endangle = min(startangle, endangle), max(startangle, endangle)
        #elif orientation == 'left':
        #    startangle, endangle = max(startangle, endangle), min(startangle, endangle)
        #else :
        startangle, endangle = min(startangle, endangle), max(startangle, endangle)
        if orientation <> "left" and orientation <> "right" :
            raise ValueError("Invalid orientation %s, should be 'left' or 'right'" \
                             % repr(orientation))

        angle = float(endangle - startangle)    # angle subtended by arc
        middle_radius = 0.5*(inner_radius+outer_radius)
        boxheight = outer_radius - inner_radius
        shaft_height = boxheight*shaft_height_ratio
        shaft_inner_radius = middle_radius - 0.5*shaft_height
        shaft_outer_radius = middle_radius + 0.5*shaft_height
        headangle_delta = min(abs(asin(boxheight/middle_radius)*head_length_ratio), abs(angle))
        if angle < 0 :
            headangle_delta *= -1 #reverse it
        if orientation=="right" :
            headangle = endangle-headangle_delta
        else :
            headangle = startangle+headangle_delta
        if startangle <= endangle :
            headangle = max(min(headangle, endangle), startangle)
        else :
            headangle = max(min(headangle, startangle), endangle)
        assert startangle <= headangle <= endangle \
            or endangle <= headangle <= startangle
        

        # Calculate trig values for angle and coordinates
        startcos, startsin = cos(startangle), sin(startangle)
        headcos, headsin = cos(headangle), sin(headangle)
        endcos, endsin = cos(endangle), sin(endangle)
        x0,y0 = self.xcenter, self.ycenter      # origin of the circle
        if abs(headangle_delta) >= abs(angle) :
            #Cheat and just use a triangle.
            if orientation=="right" :
                x1,y1 = (x0+inner_radius*startsin, y0+inner_radius*startcos)
                x2,y2 = (x0+outer_radius*startsin, y0+outer_radius*startcos)
                x3,y3 = (x0+middle_radius*endsin, y0+middle_radius*endcos)
            else :
                x1,y1 = (x0+inner_radius*endsin, y0+inner_radius*endcos)
                x2,y2 = (x0+outer_radius*endsin, y0+outer_radius*endcos)
                x3,y3 = (x0+middle_radius*startsin, y0+middle_radius*startcos)
            return draw_polygon([(x1,y1),(x2,y2),(x3,y3)], color, border)
        elif orientation=="right" :
            p = ArcPath(strokeColor=strokecolor,
                        fillColor=color,
                        strokewidth=0)
            #Note reportlab counts angles anti-clockwise from the horizontal
            #(as in mathematics, e.g. complex numbers and polar coordinates)
            #but we use clockwise from the vertical.  Also reportlab uses
            #degrees, but we use radians.
            p.addArc(self.xcenter, self.ycenter, shaft_inner_radius,
                     90 - (headangle * 180 / pi), 90 - (startangle * 180 / pi),
                     moveTo=True)
            p.addArc(self.xcenter, self.ycenter, shaft_outer_radius,
                     90 - (headangle * 180 / pi), 90 - (startangle * 180 / pi),
                     reverse=True)
            p.lineTo(x0+outer_radius*headsin, y0+outer_radius*headcos)
            p.lineTo(x0+middle_radius*endsin, y0+middle_radius*endcos)
            p.lineTo(x0+inner_radius*headsin, y0+inner_radius*headcos)
            p.closePath()
            return p
        else :
            p = ArcPath(strokeColor=strokecolor,
                        fillColor=color,
                        strokewidth=0)
            #Note reportlab counts angles anti-clockwise from the horizontal
            #(as in mathematics, e.g. complex numbers and polar coordinates)
            #but we use clockwise from the vertical.  Also reportlab uses
            #degrees, but we use radians.
            p.addArc(self.xcenter, self.ycenter, shaft_inner_radius,
                     90 - (endangle * 180 / pi), 90 - (headangle * 180 / pi),
                     moveTo=True, reverse=True)
            p.addArc(self.xcenter, self.ycenter, shaft_outer_radius,
                     90 - (endangle * 180 / pi), 90 - (headangle * 180 / pi),
                     reverse=False)
            p.lineTo(x0+outer_radius*headsin, y0+outer_radius*headcos)
            p.lineTo(x0+middle_radius*startsin, y0+middle_radius*startcos)
            p.lineTo(x0+inner_radius*headsin, y0+inner_radius*headcos)
            p.closePath()
            return p


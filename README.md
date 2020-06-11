diversify-caltech
=================

A work in progress... 


> The Truth Shall Make You Free

Responding to the Caltech GSC's recent call, this project creates a diversity
dashboard for Caltech using public data compiled from the Registrar's office.

The sole input is a spreadsheet with enrollment information by year. The data 
has been pulled from the Registar's website with prior year values (2007 onwards)
retrieved from the Wayback Machine.

Plots are generated using Holoviews (Bokeh backend) and rendered into static HTML
for severless hosting with Github Pages. This allows for interactive graphics and
easy revision in the future.

[MIT's dashboard](http://ir.mit.edu/diversity-dashboard/) (pointed to by the GSC)
uses Tableau as a backend; this is unnecessary since the data transformations are
simple. In any case, the color scheme has been used directly and the plot views as
inspiration. 


## Current plots

* [Overall](/p_dash.html)
* [UG v G](/p_level_dash.html)



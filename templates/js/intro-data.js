function startIntro() {
    var intro = introJs();
    intro.setOptions({
        steps: [
            {
                element: '.g-selectors',
                intro: "Select two gases from the drop-down list below. Materials with available isotherms on these probes are then displayed in the dashboard. Only the materials where KPI can be calculated are plotted."
            },
            {
                element: '.dtypes',
                intro: "Select which kind of data is displayed. WARNING: Not all data in the ISODB is tagged!"
            },
            {
                element: '.kpi',
                intro: "The color of the points represents by number of available isotherms, with grey denoting only one datapoint available. If clicked, the material is highlighted in all graphs and the confidence range of the KPI is displayed as dotted lines. Multiple points can be selected through the use of the table or by shift-clicking graph points.",
                position: 'right'
            },
            {
                element: '.bk-toolbar',
                intro: "Panning, zooming can be done using the mouse; reset the graph by pressing the reset button in the upper-right corner.",
                position: 'right'
            },
            {
                element: '.t-details',
                intro: 'Table with all materials. The box may be checked to select one or multiple points. Two predictors of separation performance are calculated: KH1/KH2 is the ratio of the henry constants for the two gases while PSA-API is a selection parameter similar to the one described by Rege and Yang, miltiplying the Henry constant ratio with the working capacity ratio (KH1/KH2 * WC1/WC2)',
                position: 'right'
            },
            {
                element: '.g-henry',
                intro: 'Henry constant correlation for two materials is plotted here.',
                position: 'left'
            },
            {
                element: '.g-load',
                intro: 'The uptake graph shows the amount adsorbed a particular pressure.',
                position: 'right'
            },
            {
                element: '.g-wcap',
                intro: 'Working capacity plots is the difference between uptake at two pressures',
                position: 'left'
            },
            {
                element: '.p-selectors',
                intro: "The sliders below the graphs can be used to change the pressure selected for each respective KPI",
                position: 'bottom'
            },
            {
                element: '.isotherms',
                intro: 'Once a material has been selected, the graphs at the bottom of the page display the isotherms from the ISODB database that have been used for calculations, as well as the median for each point. Click on them to be directed to the NIST page for the corresponding publication which contains detailed information about the isotherm source.',
                position: 'top'
            }
        ]
    });

    intro.start();
}
import cytoscape from "cytoscape";
import cola from "cytoscape-cola";

cytoscape.use( cola );

let cy = cytoscape({
    container: $('#cy'),
    style: [ // the stylesheet for the graph
        {
            selector: 'node',
            style: {
                'background-color': '#666',
                'label': 'data(name)'
            }
        },
        {
            selector: 'edge',
            style: {
                'width': 3,
                'line-color': '#ccc',
            }
        },
        {
            selector: 'node.active',
            style: {
                'color': 'green',
                'background-color': 'green',
                'font-size': 24,
                'font-weight': 'bold',
                'text-outline-color': 'white',
                'text-outline-opacity': 1,
                'text-outline-width': 2,
            }
        },
        {
            selector: 'node:selected',
            style: {
                'color': 'blue',
                'background-color': 'blue',
                'font-size': 24,
                'font-weight': 'bold',
                'text-outline-color': 'white',
                'text-outline-opacity': 1,
                'text-outline-width': 2,
                'z-index': 1
            }
        }
    ],
});

let current_sub = "Turkey";
load_subreddits(current_sub);

$('#search-btn').on('click', () => {
    const search_key = $('#search-input').val();
    if(!search_key || current_sub === search_key)
        return;

    load_subreddits(search_key);
});

$('#select-algorithm').on('change', () => {
    load_subreddits(current_sub);
});

function load_subreddits(search_key) {
    $('#current-sub').html(search_key + ' <span class="badge badge-success" id="num-similar"></span>');

    const algorithm = $('#select-algorithm option:selected').val();

    let url = "https://reddit-analyzed.herokuapp.com/simrank/" + search_key;
    if(algorithm === "2")
        url = "https://reddit-analyzed.herokuapp.com/cosine/" + search_key;

    $.ajax({
        url: url,
        success: function (result) {
            update_cy(search_key, result, algorithm);
        }
    });
}

function update_cy(search_key, eles, algorithm){
    $('#num-similar').html('#' + eles.length);
    current_sub = search_key;

    update_similar_list(eles);

    cy.nodes().removeClass("active");

    let elements = [];
    elements.push({
        data: {id: search_key, name: search_key},
        classes: "active"
    });

    eles.forEach(ele => {
        elements.push({
            data: {id: ele[0], name: ele[0]}
        });

        elements.push({
            data: {id: search_key + ele[0], sim: ele[1], source: search_key, target: ele[0]}
        });
    });

    cy.json({
        elements: elements
    });

    const multiplier = (algorithm === "1") ? 5 : 10;
    const options = {
        name: 'cola',
        refresh: 7,
        ungrabifyWhileSimulating: true,
        edgeLength: edge => {return multiplier / edge.data('sim')}};
    cy.layout(options).run();
}

function update_similar_list(eles){
    const similar_list = $('#similar-list');
    similar_list.empty();
    eles.forEach(ele => {
        const item = $('<li id="${ele[0]}" ' +
            'class="list-group-item d-flex justify-content-between align-items-center">' +
            ele[0] + '<span class="badge badge-light">' + ele[1].toFixed(3) + '</span></li>');
        item.on('click', () => {cy.$('#' + ele[0]).select()});
        similar_list.append(item);
    });
}
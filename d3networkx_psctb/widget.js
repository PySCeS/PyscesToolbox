define(function(require) {
    var d3 = require('https://cdnjs.cloudflare.com/ajax/libs/d3/3.4.1/d3.min.js');
    var utils = require('base/js/utils');
    var widget = require('nbextensions/jupyter-js-widgets/extension');
    var bootstrap = require('bootstrap');

    // Define the D3ForceDirectedGraphView
    var D3ForceDirectedGraphView = widget.DOMWidgetView.extend({

        /**
         * Render the widget content
         */
        render: function() {
            this.guid = 'd3force' + utils.uuid();
            this.$div = $('<div />')
                .attr('id', this.guid);
            // this.setElement($('<div />', {
            //     id: this.guid
            // }));
            this.$el.append(this.$div)

            this.model.on('msg:custom', this.on_msg, this);
            this.has_drawn = false;

            // Wait for element to be added to the DOM
            this.once('displayed', this.update, this);
            this.model.on('change:show_color_legend', this.draw_color_legend, this);
        },

        save_clicked : function() {
            this.dump_svg();
            this.send({'button_click':'save_image'});
        },

        /**
         * Adds a node if it doesn't exist yet
         * @param  {string} id - node id
         * @return {object} node, either the new node or the node that already
         *                  existed with the id specified.
         */
        try_add_node: function(id) {
            var index = this.find_node(id);
            if (index == -1) {
                var node = {
                    id: id
                };
                this.nodes.push(node);
                return node;
            } else {
                return this.nodes[index];
            }
        },

        /**
         * Update a node's attributes
         * @param  {object} node
         * @param  {object} attributes - dictionary of attribute key/values
         */
        update_node: function(node, attributes) {
            if (node !== null) {
                for (var key in attributes) {
                    if (attributes.hasOwnProperty(key)) {
                        node[key] = attributes[key];
                    }
                }
                this._update_circle(d3.select('#' + this.guid + node.id).select(['[shape=circle']));
                this._update_rect(d3.select('#' + this.guid + node.id).select(['[shape=rect']));
                this._update_text(d3.select('#' + this.guid + node.id + '-text'));
            }
        },

        /**
         * Remove a node by id
         * @param  {string} id
         */
        remove_node: function(id) {
            this.remove_links_to(id);

            var found_index = this.find_node(id);
            if (found_index != -1) {
                this.nodes.splice(found_index, 1);
            }
        },

        /**
         * Find a node's index by id
         * @param  {string} id
         * @return {integer} node index or -1 if not found
         */
        find_node: function(id) {
            for (var i = 0; i < this.nodes.length; i++) {
                if (this.nodes[i].id == id) return i;
            }
            return -1;
        },

        /**
         * Find a link's index by source and destination node ids.
         * @param  {string} source_id - source node id
         * @param  {string} target_id - destination node id
         * @return {integer} link index or -1 if not found
         */
        find_link: function(source_id, target_id) {
            for (var i = 0; i < this.links.length; i++) {
                var link = this.links[i];
                if (link.source.id == source_id && link.target.id == target_id) {
                    return i;
                }
            }
            return -1;
        },

        /**
         * Adds a link if the link could not be found.
         * @param  {string} source_id - source node id
         * @param  {string} target_id - destination node id
         * @return {object} link
         */
        try_add_link: function(source_id, target_id) {
            var index = this.find_link(source_id, target_id);
            if (index == -1) {
                var source_node = this.try_add_node(source_id);
                var target_node = this.try_add_node(target_id);
                var new_link = {
                    source: source_node,
                    target: target_node
                };
                this.links.push(new_link);
                return new_link;
            } else {
                return this.links[index];
            }
        },

        /**
         * Updates a link with attributes
         * @param  {object} link
         * @param  {object} attributes - dictionary of attribute key/value pairs
         */
        update_link: function(link, attributes) {
            if (link) {
                for (var key in attributes) {
                    if (attributes.hasOwnProperty(key)) {
                        link[key] = attributes[key];
                    }
                }
                this._update_edge(d3.select('#' + this.guid + link.source.id + "-" + link.target.id));
            }
        },

        /**
         * Remove links with a given source node id.
         * @param  {string} source_id - source node id
         */
        remove_links: function(source_id) {
            var found_indicies = [];
            var i;
            for (i = 0; i < this.links.length; i++) {
                if (this.links[i].source.id == source_id) {
                    found_indicies.push(i);
                }
            }

            // Remove the indicies in reverse order.
            found_indicies.reverse();
            for (i = 0; i < found_indicies.length; i++) {
                this.links.splice(found_indicies[i], 1);
            }
        },

        /**
         * Remove links to or from a given node id.
         * @param  {string} id - node id
         */
        remove_links_to: function(id) {
            var found_indicies = [];
            var i;
            for (i = 0; i < this.links.length; i++) {
                if (this.links[i].source.id == id || this.links[i].target.id == id) {
                    found_indicies.push(i);
                }
            }

            // Remove the indicies in reverse order.
            found_indicies.reverse();
            for (i = 0; i < found_indicies.length; i++) {
                this.links.splice(found_indicies[i], 1);
            }
        },

        /**
         * Handles custom widget messages
         * @param  {object} content - msg content
         */
        on_msg: function(content) {
            this.update();

            var dict = content.dict;
            var action = content.action;
            var key = content.key;
            console.log(dict)

            if (dict == 'node') {
                if (action == 'add' || action == 'set') {
                    this.update_node(this.try_add_node(key), content.value);
                } else if (action == 'del') {
                    this.remove_node(key);
                }

            } else if (dict == 'adj') {
                if (action == 'add' || action == 'set') {
                    var links = content.value;
                    for (var target_id in links) {
                        if (links.hasOwnProperty(target_id)) {
                            this.update_link(this.try_add_link(key, target_id), links[target_id]);
                        }
                    }
                } else if (action == 'del') {
                    this.remove_links(key);
                }
            }

            this.render_d3();
        },

        /**
         * Render the d3 graph
         */
        render_d3: function() {
            var node = this.svg.selectAll(".gnode"),
                link = this.svg.selectAll(".link");

            link = link.data(this.force.links(), function(d) {
                return d.source.id + "-" + d.target.id;
            });
            this._update_edge(link.enter().insert("path", ".gnode"));
            link.exit().remove();

            node = node.data(this.force.nodes(), function(d) {
                return d.id;
            });

            var gnode = node.enter()
                .append("g")
                .attr('class', 'gnode')
                .call(this.force.drag);

            gnode.append(function(d) {
                return document.createElementNS(d3.ns.prefix.svg, d.shape);
            }).attr("shape", function(d) {
                return d.shape;
            });
            this._update_shape();
            //this._update_circle();
            this._update_text(gnode.append("text"));
            node.exit().remove();


            this.force.start();
        },

        _update_shape: function() {
            circle = this.svg.selectAll("[shape=circle]");
            rect = this.svg.selectAll("[shape=rect]");
            this._update_rect(rect);
            this._update_circle(circle);

        },
        _update_rect: function(rect) {
            var that = this;

            rect
                .attr("id", function(d) {
                    return that.guid + d.id;
                })
                .attr("class", function(d) {
                    return "node " + d.id;
                })
                .attr("width", function(d) {
                    if (d.r === undefined) {
                        return 16;
                    } else {
                        return d.r * 2;
                    }

                })
                .attr("height", function(d) {
                    if (d.r === undefined) {
                        return 16;
                    } else {
                        return d.r * 2;
                    }

                })
                .attr('x', function(d) {
                    if (d.r === undefined) {
                        return -8;
                    } else {
                        return -d.r;
                    }
                })
                .attr('y', function(d) {
                    if (d.r === undefined) {
                        return -8;
                    } else {
                        return -d.r;
                    }
                })
                .style("fill", function(d) {
                    if (d.fill === undefined) {
                        return that.color(d.group);
                    } else {
                        return d.fill;
                    }

                })
                .style("stroke", function(d) {
                    if (d.stroke === undefined) {
                        return "#FFF";
                    } else {
                        return d.stroke;
                    }

                })
                .style("stroke-width", function(d) {
                    if (d.strokewidth === undefined) {
                        return "1.5px";
                    } else {
                        return d.strokewidth;
                    }

                });

        },
        /**
         * Updates a d3 rendered circle
         * @param  {D3Node} circle
         */
        _update_circle: function(circle) {
            var that = this;

            circle
                .attr("id", function(d) {
                    return that.guid + d.id;
                })
                .attr("class", function(d) {
                    return "node " + d.id;
                })
                .attr("r", function(d) {
                    if (d.r === undefined) {
                        return 8;
                    } else {
                        return d.r;
                    }

                })
                .style("fill", function(d) {
                    if (d.fill === undefined) {
                        return that.color(d.group);
                    } else {
                        return d.fill;
                    }

                })
                .style("stroke", function(d) {
                    if (d.stroke === undefined) {
                        return "#FFF";
                    } else {
                        return d.stroke;
                    }

                })
                .style("stroke-width", function(d) {
                    if (d.strokewidth === undefined) {
                        return "1.5px";
                    } else {
                        return d.strokewidth;
                    }

                })
                .attr('dx', 0)
                .attr('dy', 0);
        },

        /**
         * Updates a d3 rendered fragment of text
         * @param  {D3Node} text
         */
        _update_text: function(text) {
            var that = this;

            text
                .attr("id", function(d) {
                    return that.guid + d.id + '-text';
                })
                .attr("font-family", "sans-serif")
                .text(function(d) {
                    if (d.label) {
                        return d.label;
                    } else {
                        return '';
                    }
                })
                .style("font-size", function(d) {
                    if (d.font_size) {
                        return d.font_size;
                    } else {
                        return '11pt';
                    }
                })
                .attr("text-anchor", "right")
                .style("fill", function(d) {
                    if (d.color) {
                        return d.color;
                    } else {
                        return 'white';
                    }
                })
                .attr('dx', function(d) {
                    if (d.dx) {
                        return d.dx;
                    } else {
                        return 0;
                    }
                })
                .attr('dy', function(d) {
                    if (d.dy) {
                        return d.dy;
                    } else {
                        return 5;
                    }
                })
                .style("pointer-events", 'none');
        },

        /**
         * Updates a d3 rendered edge
         * @param  {D3Node} edge
         */
        _update_edge: function(edge) {
            var that = this;
            edge
                .attr("id", function(d) {
                    return that.guid + d.source.id + "-" + d.target.id;
                })
                .attr("class", "link")
                .style("stroke-width", function(d) {
                    if (d.strokewidth === undefined) {
                        return "1.5px";
                    } else {
                        return d.strokewidth;
                    }

                })
                .style('stroke', function(d) {
                    if (d.stroke === undefined) {
                        return "#999";
                    } else {
                        return d.stroke;
                    }

                })
                .style('fill', 'none')
                .attr("marker-end", function(d) {
                    if (d.marker_end === undefined) {
                        return "none";
                    } else {
                        return "url(#" + d.marker_end + ")";
                    }
                })
                .attr("marker-mid", function(d) {
                    if (d.marker_mid === undefined) {
                        return "none";
                    } else {
                        return "url(#" + d.marker_mid + ")";
                    }
                })
                .attr("stroke-dasharray", function(d) {
                    if (d.marker_end === "dagger") {
                        return "5,5";
                    } else {
                        return "none";
                    }
                })
                .attr("stroke-linecap", "round");

        },


        tick: function() {
            var gnode = this.svg.selectAll(".gnode"),
                link = this.svg.selectAll(".link");

            straight_links = this.model.get('straight_links')



            function grid(num) {
                var gridsize = 25;
                var left_overs = num % gridsize;
                if (left_overs > gridsize / 2) {
                    return num + gridsize - left_overs;
                } else {
                    return num - left_overs;
                }
            };



            link.attr("d", function(d) {

                var dx = grid(d.source.x) - grid(d.target.x),
                    dy = grid(d.source.y) - grid(d.target.y);

                var ratio = 500;
                // var ddx = d.source.x + dx/ratio;
                // var ddy = d.target.y + dy/ratio;

                if (Math.abs(dx / dy) > 1) {
                    ratio = ratio / (dx / dy)
                    var ddx = d.source.x + dx / ratio;
                    var ddy = d.target.y + dy / ratio;
                } else if (Math.abs(dx / dy) < 1) {
                    ratio = ratio * (dx / dy)
                    var ddx = d.target.x + dx / ratio;
                    var ddy = d.source.y + dy / ratio;

                }

                if (dx === 0 || dy === 0 || Math.abs(dx / dy) === 1 || straight_links === true) {
                    var ddx = grid(d.source.x);
                    var ddy = grid(d.source.y);
                }
                return "M" +
                    grid(d.source.x) + "," +
                    grid(d.source.y) + " Q" +
                    ddx + "," +
                    ddy + ", " +
                    grid(d.target.x) + "," +
                    grid(d.target.y);
            });


            // Translate the groups
            gnode.attr("transform", function(d) {
                return "translate(" + grid(d.x) + "," + grid(d.y) + ")";
            });
        },
        //*/
        dump_svg: function(){

            var svg = document.getElementById(this.guid);
            //get svg source.
            var serializer = new XMLSerializer();

            var source = serializer.serializeToString(svg);


            //add name spaces.
            if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
                source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
            }
            if (!source.match(/^<svg[^>]+"http\:\/\/www\.w3\.org\/1999\/xlink"/)) {
                source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
            }

            //add xml declaration
            source = '<?xml version="1.0" standalone="no"?>\r\n' + source;
            //console.log(source);
            this.model.set('svg_image',source);
            this.touch();


            //convert svg source to URI data scheme.
            //var url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
            //console.log(url);
        },
        dump_json: function() {

            var gnode = this.svg.selectAll(".gnode"),
                link = this.svg.selectAll(".link");

            this.model.set('gnode_json', JSON.stringify(gnode.data()));
            this.touch();
        },

        draw_color_legend: function() {

            if (this.model.get('show_color_legend') === true) {
                var height = 300,
                    width = 25
                x = 0,
                y = 0;

                this.svg.append("rect").attr('id', 'crec')
                    .attr('x', x)
                    .attr('y', y)
                    .attr("width", 25)
                    .attr("height", 300)
                    .style("fill", "url(#Spectral10)");

                this.svg.append("text").text("90 - 100").attr('id', 't1')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 1 - 10);

                this.svg.append("text").text("80 - 89").attr('id', 't2')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", (height / 10) * 2 - 10);

                this.svg.append("text").text("70 - 79").attr('id', 't3')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 3 - 10);

                this.svg.append("text").text("60 - 69").attr('id', 't4')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 4 - 10);

                this.svg.append("text").text("50 - 59").attr('id', 't5')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 5 - 10);

                this.svg.append("text").text("40 - 49").attr('id', 't6')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 6 - 10);

                this.svg.append("text").text("30 - 39").attr('id', 't7')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 7 - 10);

                this.svg.append("text").text("20 - 29").attr('id', 't8')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 8 - 10);

                this.svg.append("text").text("10 - 19").attr('id', 't9')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 9 - 10);

                this.svg.append("text").text("0 - 9").attr('id', 't10')
                    .attr("font-size", "15px")
                    .attr("font-family", "sans-serif")
                    .attr("fill", "black")
                    .attr("x", x + width + 5)
                    .attr("y", y + (height / 10) * 10 - 10);
            } else {
                this.svg.select('#t10').data([]).exit().remove()
                this.svg.select('#t9').data([]).exit().remove()
                this.svg.select('#t8').data([]).exit().remove()
                this.svg.select('#t7').data([]).exit().remove()
                this.svg.select('#t6').data([]).exit().remove()
                this.svg.select('#t5').data([]).exit().remove()
                this.svg.select('#t4').data([]).exit().remove()
                this.svg.select('#t3').data([]).exit().remove()
                this.svg.select('#t2').data([]).exit().remove()
                this.svg.select('#t1').data([]).exit().remove()
                this.svg.select('#crec').data([]).exit().remove()

            }
        },



        /**
         * Handles when the widget traits change.
         */
        update: function() {
            if (!this.has_drawn) {
                this.has_drawn = true;
                var width = this.model.get('width'),
                    height = this.model.get('height');

                this.color = d3.scale.category20();

                this.nodes = [];
                this.links = [];

                this.force = d3.layout.force()
                    .nodes(this.nodes)
                    .links(this.links)
                    .charge(function(d) {
                        if (d.charge === undefined) {
                            return -280;
                        } else {
                            return d.charge;
                        }
                    })
                    .linkDistance(function(d) {
                        if (d.distance === undefined) {
                            return 30;
                        } else {
                            return d.distance;
                        }
                    })
                    .linkStrength(function(d) {
                        if (d.strength === undefined) {
                            return 0.3;
                        } else {
                            return d.strength;
                        }
                    })
                    .size([width, height - 30])
                    .on("tick", $.proxy(this.tick, this));

                this.svg = d3.select("#" + this.guid).append("svg")
                    .attr("width", width)
                    .attr("height", height - 30);

                this.svg.append("defs").append("marker")
                    .attr("id", "arrowhead")
                    .attr("viewBox", "0 0 5 5")
                    .attr("refX", 10)
                    .attr("refY", 2)
                    .attr("markerWidth", 8)
                    .attr("markerHeight", 6)
                    .attr("orient", "auto")
                    .append("path")
                    .attr("d", "M 0,0 V 4 L6,2 Z"); //this is actual shape for arrowhead

                this.svg.append("defs").append("marker")
                    .attr("id", "arrowheadlarge")
                    .attr("viewBox", "0 0 5 5")
                    .attr("refX", 10)
                    .attr("refY", 2)
                    .attr("markerWidth", 0.8)
                    .attr("markerHeight", 0.6)
                    .attr("orient", "auto")
                    .append("path")
                    .attr("d", "M 0,0 V 4 L6,2 Z"); //this is actual shape for arrowhead

                this.svg.append("defs").append("marker")
                    .attr("id", "dagger")
                    .attr("viewBox", "0 0 5 5")
                    .attr("refX", 8)
                    .attr("refY", 2.5)
                    .attr("markerWidth", 9)
                    .attr("markerHeight", 7)
                    .attr("orient", "auto")
                    .append("path")
                    .attr("d", "M 0,0 V 5 H 0.75 V 0 Z")
                    .attr("fill", "gray");


                grad = this.svg.append("defs").append("linearGradient")
                    .attr("id", "Spectral10")
                    .attr("gradientUnits", "objectBoundingBox")
                    .attr("spreadMethod", "pad")
                    .attr("x1", "0%")
                    .attr("x2", "0%")
                    .attr("y1", "0%")
                    .attr("y2", "100%");

                grad.append("stop")
                    .attr("offset", "0.00%")
                    .attr("stop-color", "rgb(158,1,66)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "10.00%")
                    .attr("stop-color", "rgb(158,1,66)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "10.00%")
                    .attr("stop-color", "rgb(213,62,79)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "20.00%")
                    .attr("stop-color", "rgb(213,62,79)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "20.00%")
                    .attr("stop-color", "rgb(244,109,67)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "30.00%")
                    .attr("stop-color", "rgb(244,109,67)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "30.00%")
                    .attr("stop-color", "rgb(253,174,97)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "40.00%")
                    .attr("stop-color", "rgb(253,174,97)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "40.00%")
                    .attr("stop-color", "rgb(254,224,139)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "50.00%")
                    .attr("stop-color", "rgb(254,224,139)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "50.00%")
                    .attr("stop-color", "rgb(230,245,152)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "60.00%")
                    .attr("stop-color", "rgb(230,245,152)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "60.00%")
                    .attr("stop-color", "rgb(171,221,164)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "70.00%")
                    .attr("stop-color", "rgb(171,221,164)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "70.00%")
                    .attr("stop-color", "rgb(102,194,165)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "80.00%")
                    .attr("stop-color", "rgb(102,194,165)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "80.00%")
                    .attr("stop-color", "rgb(50,136,189)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "90.00%")
                    .attr("stop-color", "rgb(50,136,189)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "90.00%")
                    .attr("stop-color", "rgb(94,79,162)")
                    .attr("stop-opacity", "1.0000");
                grad.append("stop")
                    .attr("offset", "100.00%")
                    .attr("stop-color", "rgb(94,79,162)")
                    .attr("stop-opacity", "1.0000");





                this.$layout_el = $('<button />');
                this.$layout_el.text('Save Layout')

                this.$layout_btn = this.$layout_el.button().addClass('btn btn-default');
                this.$layout_btn.on("click", $.proxy(this.dump_json, this));
                this.$el.append(this.$layout_el);

                this.$img_el = $('<button />');
                this.$img_el.text('Save Image')

                this.$image_btn = this.$img_el.button().addClass('btn btn-default');
                this.$image_btn.on("click", $.proxy(this.save_clicked, this));
                this.$el.append(this.$img_el);
            }

            var that = this;
            setTimeout(function() {
                that.render_d3();
            }, 0);
            return D3ForceDirectedGraphView.__super__.update.apply(this);
        },

    });

    return {
        D3ForceDirectedGraphView: D3ForceDirectedGraphView
    };
});
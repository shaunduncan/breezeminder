(function($) {
    // The application
    var marta;

    // Stored height of fullscreen control bar - needed for one time eval
    var FS_CTRL_HEIGHT = null;


    // Backbone elements
    var POI = Backbone.Model.extend({
        initialize: function(id, pos, opts) {
            this.id = id;
            this.position = pos instanceof google.maps.LatLng ? pos: new google.maps.LatLng(pos[0], pos[1]);
            this.marker = new google.maps.Marker(_.extend({
                position: this.position,
                map: marta.map
            }, opts));

            // Boilerplate
            this.window = new google.maps.InfoWindow({
                content: opts.content ? opts.content : '<h4>' + this.marker.getTitle() + '</h4>'
            });
            this.window.poi = this;

            // Events
            google.maps.event.addListener(this.marker, 'click', $.proxy(function() {
                if(marta.map.window) {
                    google.maps.event.trigger(marta.map.window, 'closeclick');
                    marta.map.window = null;
                    marta.map.watching = null;
                }

                this.window.open(marta.map, this.marker);
                marta.map.window = this.window;

                // Invoke custom callback
                if(this.onClick) this.onClick();
            }, this));

            google.maps.event.addListener(this.window, 'closeclick', $.proxy(function() {
                if(this.window) this.window.close();
                if(this.onClose) this.onClose();
            }, this));
        },

        // Safely set POI position
        setPosition: function(pos) {
            if(pos) {
                this.position = pos;
                this.marker.setPosition(this.position);
            }
            return this;
        },

        // Simulate marker click
        click: function() {
            google.maps.event.trigger(this.marker, 'click');
            return this;
        },

        // Simulate marker click
        close: function() {
            google.maps.event.trigger(this.window, 'closeclick');
            return this;
        },

        // Callbacks
        onClick: function() {},
        onClose: function() {},

        // Returns true if POI positions are "equal"
        equals: function(poi, exact) {
            if(exact) {
                return this.position.equals(poi.position);
            } else {
                return this.distance(poi) < 1;
            }
        },

        // Returns the closer POI `a` or `b` to this POI
        closer: function(a, b) {
            return this.distance(a) < this.distance(b) ? a : b;
        },

        // Distance from this POI to another POI
        distance: function(poi, readable) {
            var dist = google.maps.geometry.spherical.computeDistanceBetween(this.position, poi.position);
            if(readable) {
                dist *= 3.28084;  // m to ft
                if(dist > 1000) {
                    return (dist/5280.0).toFixed(1) + 'mi';
                } else {
                    return Math.round(dist) + 'ft';
                }
            } else {
                return dist;
            }
        },

        // Safely sets window content to reduce flicker
        setWindowContent: function($content) {
            if($content.html() != this.window.getContent()) {
                this.window.setContent($content.html());
            }
            $content.remove();
        },

        // jQuery compat window content
        getWindowContent: function() {
            return $('<div></div>').append(this.window.getContent());
        },

        // Proxies a different InfoWindow
        proxy: function(win) {
            if(!this._window) {
                this._window = this.window;
            }
            this.window = win;
            return this;
        },

        // Establishes original unproxied window
        unproxy: function() {
            if(this._window) {
                this.window = this._window;
                this._window = null;
            }
            return this;
        },

        // Focuses the map on this POI and opens the window
        focus: function(pos) {
            if(pos) this.setPosition(pos);
            marta.map.focus(this.position);
            return this.click();
        },

        // Cleanly delete this POI
        delete: function() {
            this.marker.setMap(null);
            this.marker = null;
            this.position =null;
            this.window = null;
            return this;
        }
    });

    var Stop = POI.extend({
        onClick: function() {
            var $content = this.getWindowContent()

            // Ensure control links are available for non-watched stops
            if(marta.me && marta.me.window != this.window) {
                $content.find('div.geo-controls').html(marta.TPL.markme({stop: this.id}));
            }

            // Get bus info
            $content.find('div.bus-status').html(marta.nextBus(this));

            this.setWindowContent($content);
        }
    });

    var Bus = POI.extend({
        onClick: function() {
            if(marta.me) {
                $content = this.getWindowContent();
                $content.find('span.distance').html(this.distance(marta.me, true) + ' Away');
                this.setWindowContent($content);
            }
            marta.map.watching = this;
            marta.map.focus(this.position);
        }
    });


    var POISet = Backbone.Collection.extend({model: POI});


    // Marta constructor
    var Marta = function(div) {
        this.$div = $('#' + div);
        this.socket = window.Juggernaut ? new Juggernaut() : null;

        // Fit the div to the screen
        this.fit();

        // Map-related items
        this.routeId = this.$div.attr('data-route'); 

        // Bookkeeping
        this.stops = new POISet();
        this.buses = new POISet();
        this.me = null;
        this.TPL = {};
    }


    Marta.fn = Marta.prototype;


    // Load mustache templates from DOM
    Marta.fn.loadTemplates = function() {
        var that = this;

        $('#templates > div.template').each(function() {
            var $el = $(this);
            that.TPL[$el.attr('data-name')] = Mustache.compile($el.html());
        });

        $('#templates').remove();
    }


    // Render the Google Map component
    Marta.fn.render = function() {
        this.progress = new ProgressDialog(2, true);
        this.progress.step('Please wait while the application is loaded');

        this.map = new google.maps.Map(this.$div.get(0), {
            zoom: 15,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            mapTypeControl: false,
            center: new google.maps.LatLng(33.745111,-84.390621)  // Atlanta
        });

        // AdSense
        if(window.adsense_pub_id) {
            new google.maps.adsense.AdUnit(document.createElement('div'), {
                backgroundColor: '#FFFFFF',
                borderColor: '#FFFFFF',
                titleColor: '#D44413',
                textColor: '#333333',
                urlColor: '#0066CC',
                map: this.map,
                visible: true,
                publisherId: window.adsense_pub_id,
                format: $(window).width < 800 ?
                    google.maps.adsense.AdFormat.SMALL_HORIZONTAL_LINK_UNIT :
                    google.maps.adsense.AdFormat.LARGE_HORIZONTAL_LINK_UNIT,
                position: google.maps.ControlPosition.TOP,
            });
        }

        // Load callback
        google.maps.event.addListenerOnce(this.map, 'idle', $.proxy(this.initialize, this));
    }


    // Gets the "real" height of the viewport (browser safe)
    Marta.fn.height = function() {
        window.scrollTo(0, 0);
        return window.innerHeight;
    }


    // Swaps content from a into b if b has no content
    Marta.fn.swap = function(a, b) {
        if(b.children().length == 0) {
            b.append(a.children().remove());
        }
    }


    // Fits the map div in the page in a smart way
    Marta.fn.fit = function() {
        var center = this.map ? this.map.getCenter() : null;

        if(!this.$div.hasClass('fullscreen')) {
            var max = $(window).height() * 0.75;

            // Content switch if needed
            this.swap($('#map-modal'), $('#map-content'));

            this.$div.css('height', max + 'px');
            $('#fullscreen-ctrl, #map-modal').hide();
        } else {
            var viewport = this.height();

            // Set this only once!
            FS_CTRL_HEIGHT = FS_CTRL_HEIGHT || $('#fullscreen-ctrl').height();

            var offsetHeight = (viewport - FS_CTRL_HEIGHT) + 'px';

            // Content switch if needed
            this.swap($('#map-content'), $('#map-modal'));

            $('#map, #map-modal').css('height', offsetHeight).show();
            $('#fullscreen-ctrl').css('top', offsetHeight).show();
        }

        if(this.map) {
            this.map.resize();
            this.map.setCenter(center);
        }
    }


    // Map load callback. Initializes the entire application
    Marta.fn.initialize = function() {
        this.loadTemplates();

        $.ajax({
            url: '/marta/route/' + this.routeId + '.json',
            context: this,
            dataType: 'json',
            success: function(route) {
                this.drawShapes(route.shapes);
                this.drawStops(route.stops);
                this.loadSchedule();
                this.loadBuses();

                this.geolocate(function() {
                    this.subscribe();
                    this.finalize();
                });
            }
        });
    }


    // Subscription for push notifications with poll fallback
    Marta.fn.subscribe = function() {
        var handler = $.proxy(this.loadBuses, this);
        var scrubber = $.proxy(function(ids) {
            _.each(ids, function(id) {
                if(this.buses.get(id)) {
                    this.buses.get(id).close().delete();
                }
            }, this);
        }, this);

        // This is magic so should node fail, we can still serve the page
        if(this.socket) {
            this.socket.subscribe('marta', handler);
            this.socket.subscribe('marta/stale', scrubber);
        } else {
            // Poll once every 30 seconds
            setInterval(handler, 30000);
        }
    }


    // Geolocation
    Marta.fn.geolocate = function(cb) {
        var that = this;
        var geoError = function(err) {
            new ModalDialog('Geolocation Error',
                'Your exact location could not be determined. You will not be'
                + 'able to view next and near bus information. You can still'
                + 'choose a stop as your current position by clicking the button'
                + 'to show stops and selecting one from the map'
            ).onDestroy(function() {
                $('.geo-error').show();
                cb.call(that);
            }).show();
        }

        if(navigator) {
            navigator.geolocation.getCurrentPosition(function(loc) {
                var focus = that.me ? false : true;
                that.initMe.call(that, loc.coords.latitude, loc.coords.longitude);

                if(focus) {
                    that.me.focus();
                }

                $('.geo-error').hide();
                cb.call(that);
            }, geoError, {
                enableHighAccuracy: false,
                timeout: 30000,
                maximumAge: 0
            });
        } else {
            geoError();
        }
    }


    // Initialize 'me' thing
    Marta.fn.initMe = function(lat, lng) {
        if(!lat && !lng) return;

        var pos = lat;

        if(!(pos instanceof google.maps.LatLng)) {
            pos = new google.maps.LatLng(lat, lng);
        }

        // Just update position if we already exist
        if(this.me) {
            this.me.setPosition(pos);
            return;
        }

        this.me = new POI('me', pos, {
            title: 'You Are Here',
            icon: '/static/images/maps/star.png',
            zIndex: 10000,
            content: this.TPL.me()
        });

        this.me.onClick = function() {
            marta.nextBus.call(marta, marta.me);
        }
    }


    // Gets the next buses to a given POI
    Marta.fn.nextBus = function(poi) {
        if(!this.buses.length || !poi) return '';

        // Returns the closer of two POIs
        var closer = function(a, b) {
            if(a && poi.closer(a, b).equals(a, true)) {
                return a;
            }
            return b;
        }

        var nearList =_.chain(this.buses.models)
            .groupBy('direction')
            .map(function(bus) { return _.reduce(bus, closer); })
            .sortBy('direction')
            .value();

        var nextList = _.chain(this.buses.models)
            .filter(function(bus) {
                // Remove buses that aren't headed towards us
                switch(bus.direction.toUpperCase()) {
                    case 'NORTHBOUND':
                        return bus.position.lat() < poi.position.lat();
                    case 'SOUTHBOUND':
                        return bus.position.lat() > poi.position.lat();
                    case 'EASTBOUND':
                        return bus.position.lng() < poi.position.lng();
                    case 'WESTBOUND':
                        return bus.position.lng() > poi.position.lng();
                }
            })
            .groupBy('direction')
            .map(function(bus) { return _.reduce(bus, closer); })
            .sortBy('direction')
            .value();

        var content = this.TPL.busStatus({'near': nearList, 'next': nextList});

        if(poi == this.me) {
            var $content = this.me.getWindowContent();
            $content.find('div.bus-status').html(content);
            this.me.setWindowContent($content);

            // Update globally
            $('div.ctrl-bus-status').html(content);
        }

        return content;
    }


    // Draw shape related elements
    Marta.fn.drawShapes = function(shapes) {
        this.shapeBounds = new google.maps.LatLngBounds();
        for(var i = 0; i < shapes.length; i++) {
            var points = [];
            for(var j = 0; j < shapes[i].length; j++) {
                var pt = new google.maps.LatLng(shapes[i][j][0], shapes[i][j][1]);
                this.shapeBounds.extend(pt);
                points.push(pt);
            }

            new google.maps.Polyline({
                strokeColor: '#519817',
                strokeOpacity: 1,
                strokeWeight: 6,
                map: this.map,
                path: points
            });
        }
    }


    // Draw all stops
    Marta.fn.drawStops = function(stops) {
        var cfg = {
            icon: '/static/images/maps/busstop-blue.png',
            visible: false
        };

        for(var i = 0; i < stops.length; i++) {
            this.stops.add(new Stop(stops[i].id, stops[i].pt, _.extend(cfg, {
                title: stops[i].name,
                content: this.TPL.stopInfo({title: stops[i].name})
            })));
        }
    }


    // Fetches current bus locations
    Marta.fn.loadBuses = function(data) {
        if(data) {
            _.each(data, this.handleBus, this);
            this.nextBus(this.me);
        } else {
            $.ajax({
                url: '/marta/realtime/' + this.routeId + '.json',
                context: this,
                dataType: 'json',
                success: function(data) {
                    _.each(data, this.handleBus, this);
                    this.nextBus(this.me);
                }
            });
        }
    }


    // Handles what to do for an individual bus
    Marta.fn.handleBus = function(data) {
        var bus = this.buses.get(data.id);
        var ctx = {};

        if(data.route != this.routeId) {
            if(bus) this.buses.remove(bus.close().delete());
            return;
        }

        if(!bus) {
            bus = new Bus(data.id, data.location, {
                icon: '/static/images/maps/bus-red.png',
                visible: true,
                zIndex: 10000,
                title: 'Bus ' + data.id
            });

            this.buses.add(bus);
        } else {
            var pt = new google.maps.LatLng(data.location[0], data.location[1]);
            if(!bus.position.equals(pt)) {
                bus.setPosition(pt);

                if(this.map.watching == bus) {
                    this.map.focus(bus.position);
                }
            }
        }

        // Every time. Update the window content maybe
        _.extend(ctx, {
            id: data.id,
            direction: data.direction,
            statusTime: data.status_time,
            schedule: 'On Time',
            color: 'darkgreen'
        });

        if(data.adherence < 0) {
            ctx.schedule = Math.abs(data.adherence) + ' Minutes Behind Schedule';
            ctx.color = 'red';
        } else if(data.adherence > 0) {
            ctx.schedule = data.adherence + ' Minutes Ahead of Schedule';
            ctx.color = '#344697';
        }

        if(this.me) ctx.distance = this.me.distance(bus, true);

        bus.direction = data.direction;
        bus.setWindowContent($('<div></div>').append(this.TPL.busInfo(ctx)));
    }


    // Fetches stop times for bus stops
    Marta.fn.loadSchedule = function(stopID) {
        var that = this;
        var args = stopID ? {'stop': stopID} : {};
        var async = stopID ? true : false;

        $.ajax({
            url: '/marta/upcoming/' + this.routeId + '.json',
            data: args,
            context: this,
            dataType: 'json',
            async: async,
            success: function(resp) {
                _.each(resp, function(data, id) {
                    var stop = this.stops.get(id);
                    var $content = stop.getWindowContent();

                    $content.find('div.bus-schedule').html(this.TPL.busSchedule({times: data.times}));
                    $content.find('div.geo-controls').html(
                        this.me && this.me.window == stop.window ?
                        this.TPL.geo() :
                        this.TPL.markme({stop: stop.id})
                    );
                    stop.setWindowContent($content);

                    // Reload this stop later
                    setTimeout((function(id) {
                        return function() {
                            that.loadSchedule(id);
                        }
                    })(id), data.refresh * 1000);
                }, this);
            }
        });
    }


    // Single container for data-action control clicks
    Marta.fn.handleActions = function($el) {
        var e = $el.attr('data-action');
        var id = $el.attr('data-id');

        if(e == 'stops') {
            $('span[data-action='+e+']').toggleClass('active');
            _.each(this.stops.models, function(stop) {
                stop.marker.setVisible(!stop.close().marker.getVisible());
            });
        } else if(e == 'fullscreen') {
            this.$div.toggleClass('fullscreen');
            this.fit();
        } else if(e == 'findme' && this.me) {
            this.me.click();
            this.map.focus(this.me.position);
        } else if(e == 'geolocate') {
            this.me.close().unproxy();
            this.geolocate(function() {
                // If geolocation fails, don't break
                if($('.geo-error').is(':visible')) {
                    this.me.close().delete();
                    this.me = null;
                    $('div.ctrl-bus-status').empty();
                } else {
                    this.me.focus();
                }
            });
        } else if(e == 'markme') {
            // Set the home marker position
            var stop = this.stops.get(id);
            var $content = stop.getWindowContent();
            $content.find('div.geo-controls').html(this.TPL.geo());
            stop.setWindowContent($content);

            if(!this.me) this.initMe(stop.position);
            this.me.proxy(stop.window).focus(stop.position);
            $('.geo-error').hide();
        } else if(e == 'watchbus' && this.buses.get(id)) {
            this.buses.get(id).click();
        }
    }


    // Finalize the app loading: controls, event handlers, etc
    Marta.fn.finalize = function() {
        var that = this;

        $('.map-control, #map, #map-modal').delegate('span, a', 'click', function() {
            that.handleActions($(this));
        });

        // Only show these by default
        $('.map-control, #map').show();

        if(this.me) {
            this.map.focus(this.me.position);
        } else {
            this.map.fitBounds(this.shapeBounds);
        }

        this.progress.complete();
        this.progress = null;
    }


    // Monkey patch google maps
    function patch() {
        _.extend(google.maps.Map.prototype, {
            // Pan to a given point and maybe zooms
            focus: function(pt, zoom) {
                zoom = zoom || 15;
                this.panTo(pt);
                if(this.getZoom() < zoom) {
                    this.setZoom(zoom);
                }
            },

            // Shorthand trigger resize event
            resize: function() {
                google.maps.event.trigger(this, 'resize');
            }

        });
    }


    // And here...we...go!
    $(document).ready(function() {
        if(window.google) {
            patch();
            marta = new Marta('map');
            marta.render();

            // Smart map div resizing
            $(window).resize(_.debounce($.proxy(marta.fit, marta), 100));

            window.marta = marta;
        } else {
            new ModalDialog('Unexpected Error',
                'Google Maps is unavailable at this time. Please try again later'
            ).onDestroy(function() {
                window.location = '/marta';
            }).show();
        }
    });
})(jQuery);

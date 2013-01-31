(function($, global) {

    global.ModalDialog = function(title, content, show) {
        this.el = this._create(title, content);

        if(show) {
            this.show();
        }
    }

    ModalDialog.fn = ModalDialog.prototype;

    /*
     * Creates the dialog in the DOM
     */
    ModalDialog.fn._create = function(title, content) {
        var id = 'modal' + (new Date()).getTime();

        // Create the modal target
        $('body').append('<div id="' + id + '" class="modal hide">'
            + '<div class="modal-header">'
            + '<button type="button" class="close" data-dismiss="modal">×</button>'
            + '<h3>' + title + '</h3></div><div class="modal-body"><p>' + content + '</p></div>'
            + '<div class="modal-footer">'
            + '<button class="btn" data-dismiss="modal">OK</button></div></div>');

        return $('#' + id);
    }

    /*
     * Sets the title
     */
    ModalDialog.fn.setTitle = function(title) {
        this.el.find('h3').html(title);
    }

    /*
     * Sets the content
     */
    ModalDialog.fn.setContent = function(content) {
        this.el.find('p').html(title);
    }

    /*
     * Shows the dialog
     */
    ModalDialog.fn.show = function() {
        this.el.modal();

        // Make sure to clean up the DOM
        this.el.on('hidden', $.proxy(this.destroy, this));
    }

    /*
     * Removes the dialog from the DOM
     */
    ModalDialog.fn.destroy = function() {
        this.el.modal('hide');
        this.el.remove();

        if(this.destroyCB) {
            this.destroyCB();
        }
    }

    /*
     * On Destroy Callback
     */
    ModalDialog.fn.onDestroy = function(fn) {
        this.destroyCB = fn;
        return this;
    }

})(jQuery, this);

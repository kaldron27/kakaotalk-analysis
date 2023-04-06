
(function(l, r) { if (!l || l.getElementById('livereloadscript')) return; r = l.createElement('script'); r.async = 1; r.src = '//' + (self.location.host || 'localhost').split(':')[0] + ':35729/livereload.js?snipver=1'; r.id = 'livereloadscript'; l.getElementsByTagName('head')[0].appendChild(r) })(self.document);
var app = (function () {
    'use strict';

    function noop() { }
    function add_location(element, file, line, column, char) {
        element.__svelte_meta = {
            loc: { file, line, column, char }
        };
    }
    function run(fn) {
        return fn();
    }
    function blank_object() {
        return Object.create(null);
    }
    function run_all(fns) {
        fns.forEach(run);
    }
    function is_function(thing) {
        return typeof thing === 'function';
    }
    function safe_not_equal(a, b) {
        return a != a ? b == b : a !== b || ((a && typeof a === 'object') || typeof a === 'function');
    }
    function is_empty(obj) {
        return Object.keys(obj).length === 0;
    }
    function append(target, node) {
        target.appendChild(node);
    }
    function insert(target, node, anchor) {
        target.insertBefore(node, anchor || null);
    }
    function detach(node) {
        if (node.parentNode) {
            node.parentNode.removeChild(node);
        }
    }
    function destroy_each(iterations, detaching) {
        for (let i = 0; i < iterations.length; i += 1) {
            if (iterations[i])
                iterations[i].d(detaching);
        }
    }
    function element(name) {
        return document.createElement(name);
    }
    function text(data) {
        return document.createTextNode(data);
    }
    function space() {
        return text(' ');
    }
    function listen(node, event, handler, options) {
        node.addEventListener(event, handler, options);
        return () => node.removeEventListener(event, handler, options);
    }
    function attr(node, attribute, value) {
        if (value == null)
            node.removeAttribute(attribute);
        else if (node.getAttribute(attribute) !== value)
            node.setAttribute(attribute, value);
    }
    function children(element) {
        return Array.from(element.childNodes);
    }
    function set_input_value(input, value) {
        input.value = value == null ? '' : value;
    }
    function custom_event(type, detail, { bubbles = false, cancelable = false } = {}) {
        const e = document.createEvent('CustomEvent');
        e.initCustomEvent(type, bubbles, cancelable, detail);
        return e;
    }

    let current_component;
    function set_current_component(component) {
        current_component = component;
    }

    const dirty_components = [];
    const binding_callbacks = [];
    let render_callbacks = [];
    const flush_callbacks = [];
    const resolved_promise = /* @__PURE__ */ Promise.resolve();
    let update_scheduled = false;
    function schedule_update() {
        if (!update_scheduled) {
            update_scheduled = true;
            resolved_promise.then(flush);
        }
    }
    function add_render_callback(fn) {
        render_callbacks.push(fn);
    }
    // flush() calls callbacks in this order:
    // 1. All beforeUpdate callbacks, in order: parents before children
    // 2. All bind:this callbacks, in reverse order: children before parents.
    // 3. All afterUpdate callbacks, in order: parents before children. EXCEPT
    //    for afterUpdates called during the initial onMount, which are called in
    //    reverse order: children before parents.
    // Since callbacks might update component values, which could trigger another
    // call to flush(), the following steps guard against this:
    // 1. During beforeUpdate, any updated components will be added to the
    //    dirty_components array and will cause a reentrant call to flush(). Because
    //    the flush index is kept outside the function, the reentrant call will pick
    //    up where the earlier call left off and go through all dirty components. The
    //    current_component value is saved and restored so that the reentrant call will
    //    not interfere with the "parent" flush() call.
    // 2. bind:this callbacks cannot trigger new flush() calls.
    // 3. During afterUpdate, any updated components will NOT have their afterUpdate
    //    callback called a second time; the seen_callbacks set, outside the flush()
    //    function, guarantees this behavior.
    const seen_callbacks = new Set();
    let flushidx = 0; // Do *not* move this inside the flush() function
    function flush() {
        // Do not reenter flush while dirty components are updated, as this can
        // result in an infinite loop. Instead, let the inner flush handle it.
        // Reentrancy is ok afterwards for bindings etc.
        if (flushidx !== 0) {
            return;
        }
        const saved_component = current_component;
        do {
            // first, call beforeUpdate functions
            // and update components
            try {
                while (flushidx < dirty_components.length) {
                    const component = dirty_components[flushidx];
                    flushidx++;
                    set_current_component(component);
                    update(component.$$);
                }
            }
            catch (e) {
                // reset dirty state to not end up in a deadlocked state and then rethrow
                dirty_components.length = 0;
                flushidx = 0;
                throw e;
            }
            set_current_component(null);
            dirty_components.length = 0;
            flushidx = 0;
            while (binding_callbacks.length)
                binding_callbacks.pop()();
            // then, once components are updated, call
            // afterUpdate functions. This may cause
            // subsequent updates...
            for (let i = 0; i < render_callbacks.length; i += 1) {
                const callback = render_callbacks[i];
                if (!seen_callbacks.has(callback)) {
                    // ...so guard against infinite loops
                    seen_callbacks.add(callback);
                    callback();
                }
            }
            render_callbacks.length = 0;
        } while (dirty_components.length);
        while (flush_callbacks.length) {
            flush_callbacks.pop()();
        }
        update_scheduled = false;
        seen_callbacks.clear();
        set_current_component(saved_component);
    }
    function update($$) {
        if ($$.fragment !== null) {
            $$.update();
            run_all($$.before_update);
            const dirty = $$.dirty;
            $$.dirty = [-1];
            $$.fragment && $$.fragment.p($$.ctx, dirty);
            $$.after_update.forEach(add_render_callback);
        }
    }
    /**
     * Useful for example to execute remaining `afterUpdate` callbacks before executing `destroy`.
     */
    function flush_render_callbacks(fns) {
        const filtered = [];
        const targets = [];
        render_callbacks.forEach((c) => fns.indexOf(c) === -1 ? filtered.push(c) : targets.push(c));
        targets.forEach((c) => c());
        render_callbacks = filtered;
    }
    const outroing = new Set();
    function transition_in(block, local) {
        if (block && block.i) {
            outroing.delete(block);
            block.i(local);
        }
    }

    const globals = (typeof window !== 'undefined'
        ? window
        : typeof globalThis !== 'undefined'
            ? globalThis
            : global);
    function mount_component(component, target, anchor, customElement) {
        const { fragment, after_update } = component.$$;
        fragment && fragment.m(target, anchor);
        if (!customElement) {
            // onMount happens before the initial afterUpdate
            add_render_callback(() => {
                const new_on_destroy = component.$$.on_mount.map(run).filter(is_function);
                // if the component was destroyed immediately
                // it will update the `$$.on_destroy` reference to `null`.
                // the destructured on_destroy may still reference to the old array
                if (component.$$.on_destroy) {
                    component.$$.on_destroy.push(...new_on_destroy);
                }
                else {
                    // Edge case - component was destroyed immediately,
                    // most likely as a result of a binding initialising
                    run_all(new_on_destroy);
                }
                component.$$.on_mount = [];
            });
        }
        after_update.forEach(add_render_callback);
    }
    function destroy_component(component, detaching) {
        const $$ = component.$$;
        if ($$.fragment !== null) {
            flush_render_callbacks($$.after_update);
            run_all($$.on_destroy);
            $$.fragment && $$.fragment.d(detaching);
            // TODO null out other refs, including component.$$ (but need to
            // preserve final state?)
            $$.on_destroy = $$.fragment = null;
            $$.ctx = [];
        }
    }
    function make_dirty(component, i) {
        if (component.$$.dirty[0] === -1) {
            dirty_components.push(component);
            schedule_update();
            component.$$.dirty.fill(0);
        }
        component.$$.dirty[(i / 31) | 0] |= (1 << (i % 31));
    }
    function init(component, options, instance, create_fragment, not_equal, props, append_styles, dirty = [-1]) {
        const parent_component = current_component;
        set_current_component(component);
        const $$ = component.$$ = {
            fragment: null,
            ctx: [],
            // state
            props,
            update: noop,
            not_equal,
            bound: blank_object(),
            // lifecycle
            on_mount: [],
            on_destroy: [],
            on_disconnect: [],
            before_update: [],
            after_update: [],
            context: new Map(options.context || (parent_component ? parent_component.$$.context : [])),
            // everything else
            callbacks: blank_object(),
            dirty,
            skip_bound: false,
            root: options.target || parent_component.$$.root
        };
        append_styles && append_styles($$.root);
        let ready = false;
        $$.ctx = instance
            ? instance(component, options.props || {}, (i, ret, ...rest) => {
                const value = rest.length ? rest[0] : ret;
                if ($$.ctx && not_equal($$.ctx[i], $$.ctx[i] = value)) {
                    if (!$$.skip_bound && $$.bound[i])
                        $$.bound[i](value);
                    if (ready)
                        make_dirty(component, i);
                }
                return ret;
            })
            : [];
        $$.update();
        ready = true;
        run_all($$.before_update);
        // `false` as a special case of no DOM component
        $$.fragment = create_fragment ? create_fragment($$.ctx) : false;
        if (options.target) {
            if (options.hydrate) {
                const nodes = children(options.target);
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                $$.fragment && $$.fragment.l(nodes);
                nodes.forEach(detach);
            }
            else {
                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                $$.fragment && $$.fragment.c();
            }
            if (options.intro)
                transition_in(component.$$.fragment);
            mount_component(component, options.target, options.anchor, options.customElement);
            flush();
        }
        set_current_component(parent_component);
    }
    /**
     * Base class for Svelte components. Used when dev=false.
     */
    class SvelteComponent {
        $destroy() {
            destroy_component(this, 1);
            this.$destroy = noop;
        }
        $on(type, callback) {
            if (!is_function(callback)) {
                return noop;
            }
            const callbacks = (this.$$.callbacks[type] || (this.$$.callbacks[type] = []));
            callbacks.push(callback);
            return () => {
                const index = callbacks.indexOf(callback);
                if (index !== -1)
                    callbacks.splice(index, 1);
            };
        }
        $set($$props) {
            if (this.$$set && !is_empty($$props)) {
                this.$$.skip_bound = true;
                this.$$set($$props);
                this.$$.skip_bound = false;
            }
        }
    }

    function dispatch_dev(type, detail) {
        document.dispatchEvent(custom_event(type, Object.assign({ version: '3.57.0' }, detail), { bubbles: true }));
    }
    function append_dev(target, node) {
        dispatch_dev('SvelteDOMInsert', { target, node });
        append(target, node);
    }
    function insert_dev(target, node, anchor) {
        dispatch_dev('SvelteDOMInsert', { target, node, anchor });
        insert(target, node, anchor);
    }
    function detach_dev(node) {
        dispatch_dev('SvelteDOMRemove', { node });
        detach(node);
    }
    function listen_dev(node, event, handler, options, has_prevent_default, has_stop_propagation, has_stop_immediate_propagation) {
        const modifiers = options === true ? ['capture'] : options ? Array.from(Object.keys(options)) : [];
        if (has_prevent_default)
            modifiers.push('preventDefault');
        if (has_stop_propagation)
            modifiers.push('stopPropagation');
        if (has_stop_immediate_propagation)
            modifiers.push('stopImmediatePropagation');
        dispatch_dev('SvelteDOMAddEventListener', { node, event, handler, modifiers });
        const dispose = listen(node, event, handler, options);
        return () => {
            dispatch_dev('SvelteDOMRemoveEventListener', { node, event, handler, modifiers });
            dispose();
        };
    }
    function attr_dev(node, attribute, value) {
        attr(node, attribute, value);
        if (value == null)
            dispatch_dev('SvelteDOMRemoveAttribute', { node, attribute });
        else
            dispatch_dev('SvelteDOMSetAttribute', { node, attribute, value });
    }
    function set_data_dev(text, data) {
        data = '' + data;
        if (text.wholeText === data)
            return;
        dispatch_dev('SvelteDOMSetData', { node: text, data });
        text.data = data;
    }
    function validate_each_argument(arg) {
        if (typeof arg !== 'string' && !(arg && typeof arg === 'object' && 'length' in arg)) {
            let msg = '{#each} only iterates over array-like objects.';
            if (typeof Symbol === 'function' && arg && Symbol.iterator in arg) {
                msg += ' You can use a spread to convert this iterable into an array.';
            }
            throw new Error(msg);
        }
    }
    function validate_slots(name, slot, keys) {
        for (const slot_key of Object.keys(slot)) {
            if (!~keys.indexOf(slot_key)) {
                console.warn(`<${name}> received an unexpected slot "${slot_key}".`);
            }
        }
    }
    /**
     * Base class for Svelte components with some minor dev-enhancements. Used when dev=true.
     */
    class SvelteComponentDev extends SvelteComponent {
        constructor(options) {
            if (!options || (!options.target && !options.$$inline)) {
                throw new Error("'target' is a required option");
            }
            super();
        }
        $destroy() {
            super.$destroy();
            this.$destroy = () => {
                console.warn('Component was already destroyed'); // eslint-disable-line no-console
            };
        }
        $capture_state() { }
        $inject_state() { }
    }

    /* src/App.svelte generated by Svelte v3.57.0 */

    const { Error: Error_1, console: console_1 } = globals;
    const file = "src/App.svelte";

    function get_each_context(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[10] = list[i];
    	return child_ctx;
    }

    function get_each_context_1(ctx, list, i) {
    	const child_ctx = ctx.slice();
    	child_ctx[10] = list[i];
    	return child_ctx;
    }

    // (72:2) {#each ranker_data as item}
    function create_each_block_1(ctx) {
    	let t0_value = /*item*/ ctx[10].ranking + "";
    	let t0;
    	let t1;
    	let t2_value = /*item*/ ctx[10].name + "";
    	let t2;
    	let t3;
    	let t4_value = /*item*/ ctx[10].count + "";
    	let t4;
    	let t5;
    	let br;

    	const block = {
    		c: function create() {
    			t0 = text(t0_value);
    			t1 = text("위: ");
    			t2 = text(t2_value);
    			t3 = text(" / (");
    			t4 = text(t4_value);
    			t5 = text(")");
    			br = element("br");
    			add_location(br, file, 72, 48, 1538);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, t0, anchor);
    			insert_dev(target, t1, anchor);
    			insert_dev(target, t2, anchor);
    			insert_dev(target, t3, anchor);
    			insert_dev(target, t4, anchor);
    			insert_dev(target, t5, anchor);
    			insert_dev(target, br, anchor);
    		},
    		p: function update(ctx, dirty) {
    			if (dirty & /*ranker_data*/ 8 && t0_value !== (t0_value = /*item*/ ctx[10].ranking + "")) set_data_dev(t0, t0_value);
    			if (dirty & /*ranker_data*/ 8 && t2_value !== (t2_value = /*item*/ ctx[10].name + "")) set_data_dev(t2, t2_value);
    			if (dirty & /*ranker_data*/ 8 && t4_value !== (t4_value = /*item*/ ctx[10].count + "")) set_data_dev(t4, t4_value);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(t0);
    			if (detaching) detach_dev(t1);
    			if (detaching) detach_dev(t2);
    			if (detaching) detach_dev(t3);
    			if (detaching) detach_dev(t4);
    			if (detaching) detach_dev(t5);
    			if (detaching) detach_dev(br);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block_1.name,
    		type: "each",
    		source: "(72:2) {#each ranker_data as item}",
    		ctx
    	});

    	return block;
    }

    // (78:2) {#each all_data as item}
    function create_each_block(ctx) {
    	let t0_value = /*item*/ ctx[10].ranking + "";
    	let t0;
    	let t1;
    	let t2_value = /*item*/ ctx[10].name + "";
    	let t2;
    	let t3;
    	let t4_value = /*item*/ ctx[10].count + "";
    	let t4;
    	let t5;
    	let br;

    	const block = {
    		c: function create() {
    			t0 = text(t0_value);
    			t1 = text("위: ");
    			t2 = text(t2_value);
    			t3 = text(" / (");
    			t4 = text(t4_value);
    			t5 = text(")");
    			br = element("br");
    			add_location(br, file, 78, 48, 1715);
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, t0, anchor);
    			insert_dev(target, t1, anchor);
    			insert_dev(target, t2, anchor);
    			insert_dev(target, t3, anchor);
    			insert_dev(target, t4, anchor);
    			insert_dev(target, t5, anchor);
    			insert_dev(target, br, anchor);
    		},
    		p: function update(ctx, dirty) {
    			if (dirty & /*all_data*/ 4 && t0_value !== (t0_value = /*item*/ ctx[10].ranking + "")) set_data_dev(t0, t0_value);
    			if (dirty & /*all_data*/ 4 && t2_value !== (t2_value = /*item*/ ctx[10].name + "")) set_data_dev(t2, t2_value);
    			if (dirty & /*all_data*/ 4 && t4_value !== (t4_value = /*item*/ ctx[10].count + "")) set_data_dev(t4, t4_value);
    		},
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(t0);
    			if (detaching) detach_dev(t1);
    			if (detaching) detach_dev(t2);
    			if (detaching) detach_dev(t3);
    			if (detaching) detach_dev(t4);
    			if (detaching) detach_dev(t5);
    			if (detaching) detach_dev(br);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_each_block.name,
    		type: "each",
    		source: "(78:2) {#each all_data as item}",
    		ctx
    	});

    	return block;
    }

    function create_fragment(ctx) {
    	let main;
    	let h1;
    	let t1;
    	let label0;
    	let t3;
    	let input0;
    	let t4;
    	let br0;
    	let t5;
    	let label1;
    	let t7;
    	let input1;
    	let t8;
    	let br1;
    	let t9;
    	let form;
    	let label2;
    	let t11;
    	let input2;
    	let t12;
    	let br2;
    	let t13;
    	let button;
    	let t15;
    	let br3;
    	let t16;
    	let div0;
    	let canvas;
    	let t17;
    	let div1;
    	let t18;
    	let br4;
    	let t19;
    	let div2;
    	let mounted;
    	let dispose;
    	let each_value_1 = /*ranker_data*/ ctx[3];
    	validate_each_argument(each_value_1);
    	let each_blocks_1 = [];

    	for (let i = 0; i < each_value_1.length; i += 1) {
    		each_blocks_1[i] = create_each_block_1(get_each_context_1(ctx, each_value_1, i));
    	}

    	let each_value = /*all_data*/ ctx[2];
    	validate_each_argument(each_value);
    	let each_blocks = [];

    	for (let i = 0; i < each_value.length; i += 1) {
    		each_blocks[i] = create_each_block(get_each_context(ctx, each_value, i));
    	}

    	const block = {
    		c: function create() {
    			main = element("main");
    			h1 = element("h1");
    			h1.textContent = "분석";
    			t1 = space();
    			label0 = element("label");
    			label0.textContent = "시작일자:";
    			t3 = space();
    			input0 = element("input");
    			t4 = space();
    			br0 = element("br");
    			t5 = space();
    			label1 = element("label");
    			label1.textContent = "종료일자:";
    			t7 = space();
    			input1 = element("input");
    			t8 = space();
    			br1 = element("br");
    			t9 = space();
    			form = element("form");
    			label2 = element("label");
    			label2.textContent = "파일:";
    			t11 = space();
    			input2 = element("input");
    			t12 = space();
    			br2 = element("br");
    			t13 = space();
    			button = element("button");
    			button.textContent = "분석시작";
    			t15 = space();
    			br3 = element("br");
    			t16 = space();
    			div0 = element("div");
    			canvas = element("canvas");
    			t17 = space();
    			div1 = element("div");

    			for (let i = 0; i < each_blocks_1.length; i += 1) {
    				each_blocks_1[i].c();
    			}

    			t18 = text("\n\t==================================================");
    			br4 = element("br");
    			t19 = space();
    			div2 = element("div");

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				each_blocks[i].c();
    			}

    			attr_dev(h1, "class", "svelte-pl8dtw");
    			add_location(h1, file, 48, 1, 1033);
    			attr_dev(label0, "for", "name");
    			add_location(label0, file, 50, 1, 1047);
    			add_location(input0, file, 51, 1, 1081);
    			add_location(br0, file, 52, 1, 1111);
    			attr_dev(label1, "for", "end");
    			add_location(label1, file, 54, 1, 1120);
    			add_location(input1, file, 55, 1, 1153);
    			add_location(br1, file, 56, 1, 1181);
    			attr_dev(label2, "for", "file");
    			add_location(label2, file, 58, 2, 1221);
    			attr_dev(input2, "type", "file");
    			attr_dev(input2, "id", "kakao_talk_zip");
    			attr_dev(input2, "name", "kakao_talk_zip");
    			add_location(input2, file, 59, 2, 1254);
    			add_location(br2, file, 61, 2, 1321);
    			attr_dev(button, "type", "submit");
    			add_location(button, file, 62, 2, 1330);
    			add_location(form, file, 57, 1, 1189);
    			add_location(br3, file, 64, 1, 1376);
    			attr_dev(canvas, "id", "resultChart");
    			add_location(canvas, file, 67, 2, 1404);
    			attr_dev(div0, "id", "chart");
    			add_location(div0, file, 66, 1, 1385);
    			attr_dev(div1, "id", "ranker");
    			add_location(div1, file, 70, 1, 1442);
    			add_location(br4, file, 75, 51, 1614);
    			attr_dev(div2, "id", "result");
    			add_location(div2, file, 76, 1, 1622);
    			add_location(main, file, 47, 0, 1025);
    		},
    		l: function claim(nodes) {
    			throw new Error_1("options.hydrate only works if the component was compiled with the `hydratable: true` option");
    		},
    		m: function mount(target, anchor) {
    			insert_dev(target, main, anchor);
    			append_dev(main, h1);
    			append_dev(main, t1);
    			append_dev(main, label0);
    			append_dev(main, t3);
    			append_dev(main, input0);
    			set_input_value(input0, /*start*/ ctx[0]);
    			append_dev(main, t4);
    			append_dev(main, br0);
    			append_dev(main, t5);
    			append_dev(main, label1);
    			append_dev(main, t7);
    			append_dev(main, input1);
    			set_input_value(input1, /*end*/ ctx[1]);
    			append_dev(main, t8);
    			append_dev(main, br1);
    			append_dev(main, t9);
    			append_dev(main, form);
    			append_dev(form, label2);
    			append_dev(form, t11);
    			append_dev(form, input2);
    			append_dev(form, t12);
    			append_dev(form, br2);
    			append_dev(form, t13);
    			append_dev(form, button);
    			append_dev(main, t15);
    			append_dev(main, br3);
    			append_dev(main, t16);
    			append_dev(main, div0);
    			append_dev(div0, canvas);
    			append_dev(main, t17);
    			append_dev(main, div1);

    			for (let i = 0; i < each_blocks_1.length; i += 1) {
    				if (each_blocks_1[i]) {
    					each_blocks_1[i].m(div1, null);
    				}
    			}

    			append_dev(main, t18);
    			append_dev(main, br4);
    			append_dev(main, t19);
    			append_dev(main, div2);

    			for (let i = 0; i < each_blocks.length; i += 1) {
    				if (each_blocks[i]) {
    					each_blocks[i].m(div2, null);
    				}
    			}

    			if (!mounted) {
    				dispose = [
    					listen_dev(input0, "input", /*input0_input_handler*/ ctx[5]),
    					listen_dev(input1, "input", /*input1_input_handler*/ ctx[6]),
    					listen_dev(form, "submit", /*submitForm*/ ctx[4], false, false, false, false)
    				];

    				mounted = true;
    			}
    		},
    		p: function update(ctx, [dirty]) {
    			if (dirty & /*start*/ 1 && input0.value !== /*start*/ ctx[0]) {
    				set_input_value(input0, /*start*/ ctx[0]);
    			}

    			if (dirty & /*end*/ 2 && input1.value !== /*end*/ ctx[1]) {
    				set_input_value(input1, /*end*/ ctx[1]);
    			}

    			if (dirty & /*ranker_data*/ 8) {
    				each_value_1 = /*ranker_data*/ ctx[3];
    				validate_each_argument(each_value_1);
    				let i;

    				for (i = 0; i < each_value_1.length; i += 1) {
    					const child_ctx = get_each_context_1(ctx, each_value_1, i);

    					if (each_blocks_1[i]) {
    						each_blocks_1[i].p(child_ctx, dirty);
    					} else {
    						each_blocks_1[i] = create_each_block_1(child_ctx);
    						each_blocks_1[i].c();
    						each_blocks_1[i].m(div1, null);
    					}
    				}

    				for (; i < each_blocks_1.length; i += 1) {
    					each_blocks_1[i].d(1);
    				}

    				each_blocks_1.length = each_value_1.length;
    			}

    			if (dirty & /*all_data*/ 4) {
    				each_value = /*all_data*/ ctx[2];
    				validate_each_argument(each_value);
    				let i;

    				for (i = 0; i < each_value.length; i += 1) {
    					const child_ctx = get_each_context(ctx, each_value, i);

    					if (each_blocks[i]) {
    						each_blocks[i].p(child_ctx, dirty);
    					} else {
    						each_blocks[i] = create_each_block(child_ctx);
    						each_blocks[i].c();
    						each_blocks[i].m(div2, null);
    					}
    				}

    				for (; i < each_blocks.length; i += 1) {
    					each_blocks[i].d(1);
    				}

    				each_blocks.length = each_value.length;
    			}
    		},
    		i: noop,
    		o: noop,
    		d: function destroy(detaching) {
    			if (detaching) detach_dev(main);
    			destroy_each(each_blocks_1, detaching);
    			destroy_each(each_blocks, detaching);
    			mounted = false;
    			run_all(dispose);
    		}
    	};

    	dispatch_dev("SvelteRegisterBlock", {
    		block,
    		id: create_fragment.name,
    		type: "component",
    		source: "",
    		ctx
    	});

    	return block;
    }

    function instance($$self, $$props, $$invalidate) {
    	let { $$slots: slots = {}, $$scope } = $$props;
    	validate_slots('App', slots, []);
    	let start;
    	let end;
    	let all_data = [];
    	let ranker_data = [];

    	const request = async endpoint => {
    		const resp = await fetch(`http://localhost:8000/kakao${endpoint}`);
    		const result = await resp.json();
    		return result;
    	};

    	const getNumberFromBackend = async no => {
    		await request(`/test/${no}`).then(json => {
    			testData = json.data;
    		});
    	};

    	const getTotalData = async no => {
    		const result = await request(`/analysis`);
    		testData = result.result;
    	};

    	const submitForm = async event => {
    		event.preventDefault();
    		const formData = new FormData(event.target);

    		fetch(`/kakao/analysis?start=${start}&end=${end}`, { method: "POST", body: formData }).then(response => {
    			if (!response.ok) {
    				throw new Error(response.statusText);
    			}

    			return response.json();
    		}).then(data => {
    			$$invalidate(2, all_data = data.result.all_result);
    			$$invalidate(3, ranker_data = data.result.top_ranker);
    		}).catch(error => {
    			console.error(error);
    		});
    	};

    	const writable_props = [];

    	Object.keys($$props).forEach(key => {
    		if (!~writable_props.indexOf(key) && key.slice(0, 2) !== '$$' && key !== 'slot') console_1.warn(`<App> was created with unknown prop '${key}'`);
    	});

    	function input0_input_handler() {
    		start = this.value;
    		$$invalidate(0, start);
    	}

    	function input1_input_handler() {
    		end = this.value;
    		$$invalidate(1, end);
    	}

    	$$self.$capture_state = () => ({
    		start,
    		end,
    		all_data,
    		ranker_data,
    		request,
    		getNumberFromBackend,
    		getTotalData,
    		submitForm
    	});

    	$$self.$inject_state = $$props => {
    		if ('start' in $$props) $$invalidate(0, start = $$props.start);
    		if ('end' in $$props) $$invalidate(1, end = $$props.end);
    		if ('all_data' in $$props) $$invalidate(2, all_data = $$props.all_data);
    		if ('ranker_data' in $$props) $$invalidate(3, ranker_data = $$props.ranker_data);
    	};

    	if ($$props && "$$inject" in $$props) {
    		$$self.$inject_state($$props.$$inject);
    	}

    	return [
    		start,
    		end,
    		all_data,
    		ranker_data,
    		submitForm,
    		input0_input_handler,
    		input1_input_handler
    	];
    }

    class App extends SvelteComponentDev {
    	constructor(options) {
    		super(options);
    		init(this, options, instance, create_fragment, safe_not_equal, {});

    		dispatch_dev("SvelteRegisterComponent", {
    			component: this,
    			tagName: "App",
    			options,
    			id: create_fragment.name
    		});
    	}
    }

    const app = new App({
    	target: document.body,
    	props: {
    		name: 'world'
    	}
    });

    return app;

})();
//# sourceMappingURL=main.js.map

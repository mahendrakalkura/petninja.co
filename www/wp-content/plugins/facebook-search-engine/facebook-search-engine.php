<?php
/*
Plugin Name: Facebook Search Engine
Plugin URI: http://petninja.co
Description: ...coming soon...
Version: 0.1
Author: Steve J.
Author URI: http://petninja.co
License: N/A
*/

if (!function_exists('add_action')) {
	die('Error #1');
}

require_once __DIR__.'/others/variables.php';

function get_pdo() {
    return new PDO(sprintf(
        'pgsql:dbname=%s;host=%s;password=%s;port=%s;user=%s',
        $GLOBALS['facebook-search-engine']['postgresql']['database'],
        $GLOBALS['facebook-search-engine']['postgresql']['hostname'],
        $GLOBALS['facebook-search-engine']['postgresql']['password'],
        $GLOBALS['facebook-search-engine']['postgresql']['port'],
        $GLOBALS['facebook-search-engine']['postgresql']['username']
    ));
}

function facebook_search_engine_activation_hook() {
    add_option('facebook_search_engine_searches', 25);
	add_option('facebook_search_engine_watchlists', 25);
}

function facebook_search_engine_register_uninstall_hook() {
    delete_option('facebook_search_engine_searches');
	delete_option('facebook_search_engine_watchlists');
}

function facebook_search_engine_admin_menu() {
    $menu = add_menu_page(
    	__('Facebook Search Engine', 'fse'),
    	__('FSE', 'fse'),
    	'manage_options',
    	'facebook-search-engine',
    	'facebook_search_engine_dashboard',
    	plugins_url('facebook-search-engine/images/icon.png')
    );
    add_action(
        sprintf('admin_print_scripts-%s', $menu),
        'facebook_search_engine_javascripts'
    );
    add_action(
        sprintf('admin_print_scripts-%s', $menu),
        'facebook_search_engine_stylesheets'
    );
    $menu = add_submenu_page(
        'facebook-search-engine',
        __('Options', 'fse'),
        __('Options', 'fse'),
        'manage_options',
        'facebook-search-engine/options',
        'facebook_search_engine_options'
    );
    add_action(
        sprintf('admin_print_scripts-%s', $menu),
        'facebook_search_engine_javascripts'
    );
    add_action(
        sprintf('admin_print_scripts-%s', $menu),
        'facebook_search_engine_stylesheets'
    );
    $menu = add_submenu_page(
        'facebook-search-engine',
        __('Status', 'fse'),
        __('Status', 'fse'),
        'manage_options',
        'facebook-search-engine/status',
        'facebook_search_engine_status'
    );
    add_action(
        sprintf('admin_print_scripts-%s', $menu),
        'facebook_search_engine_javascripts'
    );
    add_action(
        sprintf('admin_print_scripts-%s', $menu),
        'facebook_search_engine_stylesheets'
    );
    $menu = add_submenu_page(
        'facebook-search-engine',
        __('Help', 'fse'),
        __('Help', 'fse'),
        'manage_options',
        'facebook-search-engine/help',
        'facebook_search_engine_help'
    );
    add_action(
        sprintf('admin_print_scripts-%s', $menu),
        'facebook_search_engine_javascripts'
    );
    add_action(
        sprintf('admin_print_scripts-%s', $menu),
        'facebook_search_engine_stylesheets'
    );
    if (!empty($GLOBALS['submenu']['facebook-search-engine']))
    {
        $GLOBALS['submenu']['facebook-search-engine'][0][0] = 'Dashboard';
        $GLOBALS['submenu']['facebook-search-engine'][0][3] = 'Dashboard';
    }
}

function facebook_search_engine_javascripts() {
    wp_enqueue_script(
        'facebook-search-engine-vendor-angular-js',
        plugins_url('facebook-search-engine/vendor/angular.js'),
        array('jquery'),
        '1.0',
        true
    );
    wp_enqueue_script(
        'facebook-search-engine-javascripts-all-js',
        plugins_url('facebook-search-engine/javascripts/all.js'),
        array('jquery', 'facebook-search-engine-vendor-angular-js'),
        '1.0',
        true
    );
}

function facebook_search_engine_stylesheets() {
    wp_enqueue_style(
        'facebook-search-engine-stylesheets-all-css',
        plugins_url('facebook-search-engine/stylesheets/all.css'),
        array(),
        '1.0',
        'all'
    );
}

function facebook_search_engine_dashboard() {
    ?>
    <div class="wrap" ng-app="application">
        <h2><?php echo __('Facebook Search Engine - Dashboard', 'fse');?></h2>
        <div id="poststuff">
            <div id="post-body" class="metabox-holder">
                <div id="post-body-content" class="edit-form-section">
                    <div
                        class="stuffbox"
                        data-security="<?php echo wp_create_nonce(
                            $GLOBALS['facebook-search-engine']['secret']
                        ); ?>"
                        id="namediv"
                        ng-controller="dashboard"
                        >
                        <h3><?php echo __('Statistics', 'fse'); ?></h3>
                        <div class="inside">
                            <table class="widefat">
                                <tbody>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Records',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['items'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Subscriptions',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['subscriptions'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Subscriptions/Free',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['subscriptions/free'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Subscriptions/Personal',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['subscriptions/personal'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Subscriptions/Pro',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['subscriptions/pro'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Searches',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['searches'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Searches/Free',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['searches/free'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Searches/Personal',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['searches/personal'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Searches/Pro',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['searches/pro'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Watchlists',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['watchlists'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Watchlists/Free',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['watchlists/free'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Watchlists/Personal',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['watchlists/personal'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __(
                                                'Total Number of Watchlists/Pro',
                                                'fse'
                                            ); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['watchlists/pro'] !]
                                            </span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div id="major-publishing-actions">
                            <div id="publishing-action">
                                <input
                                    class="button button-primary"
                                    ng-click="refresh()"
                                    type="button"
                                    value="<?php echo __('Refresh', 'fse'); ?>"
                                    >
                            </div>
                            <div class="clear"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <?php
}

function facebook_search_engine_options() {
    $message = array();
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $searches = 0;
        if (!empty($_POST['searches'])) {
            $searches = intval($_POST['searches']);
        }
        if (!empty($searches)) {
            update_option('facebook_search_engine_searches', $searches);
        }
        $watchlists = 0;
        if (!empty($_POST['watchlists'])) {
            $watchlists = intval($_POST['watchlists']);
        }
        if (!empty($watchlists)) {
            update_option('facebook_search_engine_watchlists', $watchlists);
        }
        $message = array(
            'class' => 'updated',
            'p' => __('Your options were updated successfully.'),
        );
    }
    ?>
    <div class="wrap">
        <h2><?php echo __('Facebook Search Engine - Options', 'fse');?></h2>
        <?php if($message): ?>
            <div
                id="message"
                class="<?php echo $message['class']; ?>"
                ><p><?php echo $message['p']; ?></p></div>
        <?php endif; ?>
        <div id="poststuff">
            <div id="post-body" class="metabox-holder">
                <div id="post-body-content" class="edit-form-section">
                    <form
                        action="<?php echo $_SERVER['REQUEST_URI'];?>"
                        method="post"
                        >
                        <div class="stuffbox" id="namediv">
                            <h3>
                                <?php echo __('General Options', 'fse'); ?>
                            </h3>
                            <div class="inside">
                                <table class="form-table editcomment">
                                    <tbody>
                                        <tr valign="top">
                                            <td class="first">
                                                <label for="searches">
                                                    <?php echo __(
                                                        'Maximum Number of Saved Searches:',
                                                        'fse'
                                                    ); ?>
                                                </label>
                                            </td>
                                            <td>
                                                <input
                                                    id="searches"
                                                    name="searches"
                                                    type="text"
                                                    value="<?php echo get_option(
                                                        'facebook_search_engine_searches',
                                                        25
                                                    ); ?>"
                                                    >
                                            </td>
                                        </tr>
                                        <tr valign="top">
                                            <td class="first">
                                                <label for="watchlists">
                                                    <?php echo __(
                                                        'Maximum Number of Watchlists:',
                                                        'fse'
                                                    ); ?>
                                                </label>
                                            </td>
                                            <td>
                                                <input
                                                    id="watchlists"
                                                    name="watchlists"
                                                    type="text"
                                                    value="<?php echo get_option(
                                                        'facebook_search_engine_watchlists',
                                                        25
                                                    ); ?>"
                                                    >
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <div id="major-publishing-actions">
                                <div id="publishing-action">
                                    <input
                                        class="button button-primary"
                                        type="submit"
                                        value="<?php echo __(
                                            'Update', 'fse'
                                        ); ?>"
                                        >
                                </div>
                                <div class="clear"></div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <?php
}

function facebook_search_engine_status() {
    ?>
    <div class="wrap" ng-app="application">
        <h2><?php echo __('Facebook Search Engine - Status', 'fse');?></h2>
        <div id="poststuff">
            <div id="post-body" class="metabox-holder">
                <div id="post-body-content" class="edit-form-section">
                    <div
                        class="stuffbox"
                        data-security="<?php echo wp_create_nonce(
                            $GLOBALS['facebook-search-engine']['secret']
                        ); ?>"
                        id="namediv"
                        ng-controller="status"
                        >
                        <h3><?php echo __('Status', 'fse'); ?></h3>
                        <div class="inside">
                            <table class="widefat">
                                <tbody>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __('Spiders', 'fse'); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['spiders'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __('RDS', 'fse'); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['rds'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __('SES', 'fse'); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['ses'] !]
                                            </span>
                                        </td>
                                    </tr>
                                    <tr valign="top">
                                        <td>
                                            <?php echo __('SQS', 'fse'); ?>
                                        </td>
                                        <td class="narrow">
                                            <img
                                                ng-show="spinner"
                                                src="<?php echo plugins_url(
                                                    'facebook-search-engine/images/spinner.gif'
                                                ); ?>"
                                                >
                                            <span ng-hide="spinner">
                                                [! data['sqs'] !]
                                            </span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div id="major-publishing-actions">
                            <div id="publishing-action">
                                <input
                                    class="button button-primary"
                                    ng-click="refresh()"
                                    type="button"
                                    value="<?php echo __('Refresh', 'fse'); ?>"
                                    >
                            </div>
                            <div class="clear"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <?php
}

function facebook_search_engine_help() {
    ?>
    <div class="wrap" ng-app="application">
        <h2><?php echo __('Facebook Search Engine - Help', 'fse');?></h2>
        <div id="poststuff">
            <div id="post-body" class="metabox-holder">
                <div id="post-body-content" class="edit-form-section">
                    <div class="stuffbox" id="namediv">
                        <h3><?php echo __('Shortcode', 'fse'); ?></h3>
                        <div class="inside">
                            <pre>[facebook_search_engine]</pre>
                            <p>
                                You can place it one or more of pages and/or
                                posts.
                            </p>
                        </div>
                    </div>
                    <div class="stuffbox" id="namediv">
                        <h3><?php echo __('Error Messages', 'fse'); ?></h3>
                        <div class="inside">
                            <p>
                                <strong>403:</strong>
                                ..implies that the currently logged in user is
                                not subscribed to the requisite tier.
                                <br>
                                <strong>Note:</strong> All WordPress
                                administrators are implicitly allowed into the
                                top tier.
                            </p>
                            <p>
                                <strong>404:</strong>
                                ..implies that the requested resource is no
                                longer available.
                            </p>
                            <p>
                                <strong>500:</strong>
                                ..implies that the requested resource generated
                                an unknown error within the server.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <?php
}

function facebook_search_engine_wp_ajax_dashboard() {
    check_ajax_referer(
        $GLOBALS['facebook-search-engine']['secret'], 'security'
    );
    $free = array();
    $personal = array();
    $pro = array();
    $results = $GLOBALS['wpdb']->get_results('
        SELECT DISTINCT id AS id
        FROM wp_pmpro_memberships_users
        WHERE membership_id = 1
    ', ARRAY_A);
    if ($results) {
        foreach ($results as $result) {
            $free[] = $result['id'];
        }
    }
    $results = $GLOBALS['wpdb']->get_results('
        SELECT DISTINCT id AS id
        FROM wp_pmpro_memberships_users
        WHERE membership_id = 2
    ', ARRAY_A);
    if ($results) {
        foreach ($results as $result) {
            $personal[] = $result['id'];
        }
    }
    $results = $GLOBALS['wpdb']->get_results('
        SELECT DISTINCT id AS id
        FROM wp_pmpro_memberships_users
        WHERE membership_id = 3
    ', ARRAY_A);
    if ($results) {
        foreach ($results as $result) {
            $pro[] = $result['id'];
        }
    }
    $items = 0;
    $searches = 0;
    $searches_free = 0;
    $searches_personal = 0;
    $searches_pro = 0;
    $watchlists = 0;
    $watchlists_free = 0;
    $watchlists_personal = 0;
    $watchlists_pro = 0;
    try {
        $connection = get_pdo();
        $items = $connection
            ->query('SELECT COUNT(id) FROM items')
            ->fetchColumn();
        $searches = $connection
            ->query('SELECT COUNT(id) FROM searches')
            ->fetchColumn();
        $searches_free = $connection
            ->query(sprintf(
                'SELECT COUNT(id) FROM searches WHERE user_id IN (%s)',
                implode(',', $free)
            ))
            ->fetchColumn();
        $searches_personal = $connection
            ->query(sprintf(
                'SELECT COUNT(id) FROM searches WHERE user_id IN (%s)',
                implode(',', $personal)
            ))
            ->fetchColumn();
        $searches_pro = $connection
            ->query(sprintf(
                'SELECT COUNT(id) FROM searches WHERE user_id IN (%s)',
                implode(',', $pro)
            ))
            ->fetchColumn();
        $watchlists = $connection
            ->query('SELECT COUNT(id) FROM watchlists')
            ->fetchColumn();
        $watchlists_free = $connection
            ->query(sprintf(
                'SELECT COUNT(id) FROM watchlists WHERE user_id IN (%s)',
                implode(',', $free)
            ))
            ->fetchColumn();
        $watchlists_personal = $connection
            ->query(sprintf(
                'SELECT COUNT(id) FROM watchlists WHERE user_id IN (%s)',
                implode(',', $personal)
            ))
            ->fetchColumn();
        $watchlists_pro = $connection
            ->query(sprintf(
                'SELECT COUNT(id) FROM watchlists WHERE user_id IN (%s)',
                implode(',', $pro)
            ))
            ->fetchColumn();
    } catch (Exception $exception) {
        print $exception;
    }
    $subscriptions = $GLOBALS['wpdb']->get_var('
        SELECT COUNT(*) FROM wp_pmpro_memberships_users
    ');
    $subscriptions_free = $GLOBALS['wpdb']->get_var('
        SELECT COUNT(*) FROM wp_pmpro_memberships_users WHERE membership_id = 1
    ');
    $subscriptions_personal = $GLOBALS['wpdb']->get_var('
        SELECT COUNT(*) FROM wp_pmpro_memberships_users WHERE membership_id = 2
    ');
    $subscriptions_pro = $GLOBALS['wpdb']->get_var('
        SELECT COUNT(*) FROM wp_pmpro_memberships_users WHERE membership_id = 3
    ');
    wp_send_json(array(
        'items' => number_format($items),
        'subscriptions' => number_format($subscriptions),
        'subscriptions/free' => number_format($subscriptions_free),
        'subscriptions/personal' => number_format($subscriptions_personal),
        'subscriptions/pro' => number_format($subscriptions_pro),
        'searches' => number_format($searches),
        'searches/free' => number_format($searches_free),
        'searches/personal' => number_format($searches_personal),
        'searches/pro' => number_format($searches_pro),
        'watchlists' => number_format($watchlists),
        'watchlists/free' => number_format($watchlists_free),
        'watchlists/personal' => number_format($watchlists_personal),
        'watchlists/pro' => number_format($watchlists_pro),
    ));
    die();
}

function facebook_search_engine_wp_ajax_status() {
    $spiders = 'Success'; // TODO
    $rds = 'Failure';
    try {
        get_pdo();
        $rds = 'Success';
    } catch (Exception $exception) {
    }
    check_ajax_referer(
        $GLOBALS['facebook-search-engine']['secret'], 'security'
    );
    $ses = 'Success'; // TODO
    $sqs = 'Success'; // TODO
    wp_send_json(array(
        'spiders' => $spiders,
        'rds' => $rds,
        'ses' => $ses,
        'sqs' => $sqs,
    ));
    die();
}

function facebook_search_engine_shortcode(){
    $plan = '';
    $user = wp_get_current_user();
    $membership_id = $GLOBALS['wpdb']->get_var(sprintf('
        SELECT membership_id
        FROM wp_pmpro_memberships_users
        WHERE user_id = %d
        ORDER BY id DESC
        LIMIT 1
        OFFSET 0
    ', $user->ID));
    switch ($membership_id) {
        case 1:
            $plan = 'Free';
            break;
        case 2:
            $plan = 'Personal';
            break;
        case 3:
            $plan = 'Pro';
            break;
        default:
            if (current_user_can('manage_options')) {
                $plan = 'Pro';
            }
            break;
    }
    ob_start();
    ?>
    <div
        data-hostname="<?php
            echo $GLOBALS['facebook-search-engine']['hostname'];
        ?>"
        data-plan="<?php echo $plan; ?>"
        data-user-id="<?php echo $user->ID; ?>"
        data-user-signature="<?php echo md5(
            $GLOBALS['facebook-search-engine']['secret']
            .
            $user->ID
            .
            $GLOBALS['facebook-search-engine']['secret']
        ); ?>"
        ng-app="application"
        id="facebook-search-engine"
        >
        <img
            class="spinner"
            src="<?php echo plugins_url(
                'facebook-search-engine/images/spinner.gif'
            ); ?>"
            >
        <ng-view></ng-view>
    </div>
    <link
        href="http://<?php
                echo $GLOBALS['facebook-search-engine']['hostname'];
            ?>/resources/assets/compressed.css"
        media="all"
        rel="stylesheet"
        type="text/css"
        >
    <script
        src="http://<?php
                echo $GLOBALS['facebook-search-engine']['hostname'];
            ?>/resources/assets/compressed.js"
        type="text/javascript"
        >
    </script>
    <?php
    return ob_get_clean();
}

register_activation_hook(__FILE__, 'facebook_search_engine_activation_hook');
register_uninstall_hook(__FILE__, 'facebook_search_engine_uninstall_hook');

add_action('admin_menu', 'facebook_search_engine_admin_menu');
add_action('wp_ajax_dashboard', 'facebook_search_engine_wp_ajax_dashboard');
add_action('wp_ajax_status', 'facebook_search_engine_wp_ajax_status');
add_shortcode('facebook_search_engine', 'facebook_search_engine_shortcode');

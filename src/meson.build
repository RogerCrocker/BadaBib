pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'badabib')
gnome = import('gnome')

gnome.compile_resources('badabib',
  'badabib.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'badabib.in',
  output: 'badabib',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

badabib_sources = [
  '__init__.py',
  'application.py',
  'bibfile.py',
  'bibitem.py',
  'change.py',
  'config_manager.py',
  'customization.py',
  'default_layouts.py',
  'dialogs.py',
  'editor.py',
  'forms.py',
  'itemlist.py',
  'layout_manager.py',
  'main_widget.py',
  'menus.py',
  'preferences.py',
  'session_manager.py',
  'store.py',
  'string_manager.py',
  'watcher.py',
  'window.py',
]

install_data(badabib_sources, install_dir: moduledir)

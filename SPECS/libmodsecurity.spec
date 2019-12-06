%global commit d7101e13685efd7e7c9f808871b202656a969f4b
%{?commit:%global shortcommit %(c=%{commit}; echo ${c:0:7})}

%global orversion    1.15.8.2
%global orngxversion 1.15.8
%global ngxversion   1.17.6
%global orprefix            %{_usr}/local/openresty
%global zlib_prefix         %{orprefix}/zlib
%global pcre_prefix         %{orprefix}/pcre
%global openssl_prefix      %{orprefix}/openssl

Name: libmodsecurity
Version: 3.0.3
Release: 2%{?dist}
Summary: A library that loads/interprets rules written in the ModSecurity SecRules

License: ASL 2.0
URL: https://www.modsecurity.org/

Source0: https://github.com/SpiderLabs/ModSecurity/releases/download/v%{version}/modsecurity-v%{version}.tar.gz
Source1: http://nginx.org/download/nginx-%{orngxversion}.tar.gz
Source2: http://nginx.org/download/nginx-%{ngxversion}.tar.gz
Source3: ModSecurity-nginx-%{shortcommit}.tar.gz
Source4: https://raw.githubusercontent.com/SpiderLabs/ModSecurity/v3/master/modsecurity.conf-recommended

BuildRequires: gcc-c++
BuildRequires: make
BuildRequires: flex
BuildRequires: bison
BuildRequires: git-core
BuildRequires: ssdeep-devel
BuildRequires: pkgconfig(libxml-2.0)
BuildRequires: pkgconfig(libcurl)
BuildRequires: pkgconfig(geoip)
BuildRequires: pkgconfig(libpcre)

%if 0%{?el6}
BuildRequires: yajl-devel
BuildRequires: lmdb-devel
%else
BuildRequires: pkgconfig(yajl)
BuildRequires: pkgconfig(lmdb)
%endif

# libinjection is supposed to be bundled (same as with mod_security 2.x)
# See: https://github.com/client9/libinjection#embedding
Provides: bundled(libinjection) = 3.9.2

%description
Libmodsecurity is one component of the ModSecurity v3 project.
The library codebase serves as an interface to ModSecurity Connectors
taking in web traffic and applying traditional ModSecurity processing.
In general, it provides the capability to load/interpret rules written
in the ModSecurity SecRules format and apply them to HTTP content provided
by your application via Connectors.


%package devel
Summary: Development files for %{name}
Requires: %{name}%{?_isa} = %{version}-%{release}

%description devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package static
Summary: Development files for %{name}
Requires: %{name}%{?_isa} = %{version}-%{release}

%description static
The %{name}-static package contains static libraries for developing
applications that use %{name}.

%package nginx
Summary: libModSecurity Nginx connector for %{name}
Requires: %{name}%{?_isa} = %{version}-%{release}
BuildRequires: zlib-devel
Requires: nginx >= %{ngxversion}

%description nginx
The ModSecurity-nginx connector is the connection point between nginx and
libmodsecurity (ModSecurity v3)

The ModSecurity-nginx connector takes the form of an nginx module. The module
simply serves as a layer of communication between nginx and ModSecurity.

%package openresty
Summary: libModSecurity OpenResty connector for %{name}
Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: openresty >= %{orversion}
BuildRequires:  openresty-zlib-devel >= 1.2.11-3
BuildRequires:  openresty-openssl-devel >= 1.1.0h-1
BuildRequires:  openresty-pcre-devel >= 8.42-1

%description openresty
The ModSecurity-nginx connector is the connection point between OpenResty and
libmodsecurity (ModSecurity v3)

The ModSecurity-nginx connector takes the form of an OpenResty module. The module
simply serves as a layer of communication between OpenResty and ModSecurity.

%prep
%setup -q -n modsecurity-v%{version}
%setup -q -n modsecurity-v%{version} -T -D -a 1
%setup -q -n modsecurity-v%{version} -T -D -a 2
%setup -q -n modsecurity-v%{version} -T -D -a 3

%build
%configure --libdir=%{_libdir} --with-lmdb
%make_build

export MODSECURITY_INC=%{_builddir}/modsecurity-v%{version}/headers
export MODSECURITY_LIB=%{_builddir}/modsecurity-v%{version}/src/.libs
export NGX_IGNORE_RPATH=YES

# https://nginx.org/packages/mainline/centos/7/x86_64/RPMS/
pushd nginx-%{ngxversion}
./configure --prefix=%{_sysconfdir}/nginx --modules-path=%{_libdir}/nginx/modules --with-compat --add-dynamic-module=../ModSecurity-nginx-%{shortcommit}
make %{?_smp_mflags}
popd

# https://github.com/openresty/openresty-packaging/blob/master/rpm/SPECS/openresty.spec
pushd nginx-%{orngxversion}
./configure --prefix="%{orprefix}/nginx" \
    --with-cc-opt="-I%{zlib_prefix}/include -I%{pcre_prefix}/include -I%{openssl_prefix}/include" \
    --with-ld-opt="-L%{zlib_prefix}/lib -L%{pcre_prefix}/lib -L%{openssl_prefix}/lib -Wl,-rpath,%{zlib_prefix}/lib:%{pcre_prefix}/lib:%{openssl_prefix}/lib" \
    --with-compat --add-dynamic-module=../ModSecurity-nginx-%{shortcommit}
make %{?_smp_mflags}
popd

%install
%make_install

pushd nginx-%{ngxversion}
mkdir -p %{buildroot}%{_libdir}/nginx/modules
cp objs/ngx_http_modsecurity_module.so %{buildroot}%{_libdir}/nginx/modules/ngx_http_modsecurity_module.so
popd

# https://www.nginx.com/blog/compiling-and-installing-modsecurity-for-open-source-nginx/
install -m 750 -d %{buildroot}%{_sysconfdir}/nginx/modsec
install -m 640 %{SOURCE4} %{buildroot}%{_sysconfdir}/nginx/modsec/modsecurity.conf

pushd nginx-%{orngxversion}
mkdir -p %{buildroot}%{orprefix}/nginx/modules
cp objs/ngx_http_modsecurity_module.so %{buildroot}%{orprefix}/nginx/modules/ngx_http_modsecurity_module.so
popd

install -m 750 -d %{buildroot}%{orprefix}/nginx/conf/modsec
install -m 640 %{SOURCE4} %{buildroot}%{orprefix}/nginx/conf/modsec/modsecurity.conf

# TODO: https://www.linuxjournal.com/content/modsecurity-and-nginx

%ldconfig_scriptlets

%files
%doc README.md AUTHORS
%{_libdir}/*.so.*
%{_bindir}/*
%license LICENSE

%files devel
%doc README.md AUTHORS
%{_includedir}/*
%{_libdir}/*.so
%{_libdir}/pkgconfig
%license LICENSE

%files static
%{_libdir}/*.a
%{_libdir}/*.la

%files nginx
%{_libdir}/nginx/modules/ngx_http_modsecurity_module.so
%{_sysconfdir}/nginx/modsec/modsecurity.conf

%files openresty
%{orprefix}/nginx/modules/ngx_http_modsecurity_module.so
%{orprefix}/nginx/conf/modsec/modsecurity.conf

%changelog
* Fri Dec  6 2019 Alexander Ursu <alexander.ursu@gmail.com> - 3.0.3-3
- Added Nginx and OpenResty connectors

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 3.0.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Sun Mar 31 2019 Athmane Madjoudj <athmane@fedoraproject.org> - 3.0.3-1
- Update to 3.0.3 (rhbz #1672678)
- Remove pkg-config bits since it's included in this release

* Fri Feb 01 2019 Fedora Release Engineering <releng@fedoraproject.org> - 3.0.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Fri Oct 19 2018 Dridi Boukelmoune <dridi@fedoraproject.org> - 3.0.2-4
- Back-port of modsecurity.pc

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.0.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Sun Apr 29 2018 Athmane Madjoudj <athmane@fedoraproject.org> - 3.0.2-2
- Rebuild after PR#1

* Sat Apr 14 2018 Athmane Madjoudj <athmane@fedoraproject.org> - 3.0.2-1
- Update to 3.0.2 (rhbz #1563219)

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3.0.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Sun Jan 21 2018 Athmane Madjoudj <athmane@fedoraproject.org> - 3.0.0-1
- Update to 3.0.0 final release
- Drop upstreamed patch
- Add some new BRs

* Sun Oct 22 2017 Athmane Madjoudj <athmane@fedoraproject.org> - 3.0.0-0.2.rc1
- Add a patch to fix the build on non-x86 arch

* Fri Sep 01 2017 Athmane Madjoudj <athmane@fedoraproject.org> - 3.0.0-0.1.rc1
- Fix release tag

* Wed Aug 30 2017 Athmane Madjoudj <athmane@fedoraproject.org> - 3.0.0-0.rc1
- Update to RC1
- Fix some spec issues

* Mon Feb 22 2016 Athmane Madjoudj <athmane@fedoraproject.org> 3.0-0.git
- Initial release


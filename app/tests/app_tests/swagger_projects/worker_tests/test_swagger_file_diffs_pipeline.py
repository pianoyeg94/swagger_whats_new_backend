import dictdiffer


class TestSwaggerFileDiffsPipeline:
    
    def test_filter_diff_method(self, swagger_file_diffs_pipeline, sink_factory):
        sink, results = sink_factory()
        filter_additions = swagger_file_diffs_pipeline.filter_diff(
            lambda diffr: diffr[0] == 'add',
            sink
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            filter_additions.send(diff)
        
        results = [result[0] for result in results]
        results_set = set(results)
        filter_additions.close()
        
        assert len(results) == 5
        assert len(results_set) == 1
        assert 'add' in results_set
    
    def test_endpoints_route_to_transformers_method(self, sink_factory,
                                                    swagger_file_diffs_pipeline):
        sink, results = sink_factory()
        dummy_sink, _ = sink_factory()
        
        route_to_transformers = swagger_file_diffs_pipeline.route_to_transformers(
            endpoint_diff=sink,
            contract_properties_diff=dummy_sink,
            contract_diff=dummy_sink,
            method_diff=dummy_sink
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            route_to_transformers.send(diff)
        
        results = [result[2][0][0] for result in results]
        route_to_transformers.close()
        
        assert len(results) == 2
        assert '/pet/{petId}/uploadImage' in results
        assert '/pet/{petId}/uploadFile' in results
    
    def test_methods_route_to_transformers_method(self, sink_factory,
                                                  swagger_file_diffs_pipeline):
        sink, results = sink_factory()
        dummy_sink, _ = sink_factory()
        
        route_to_transformers = swagger_file_diffs_pipeline.route_to_transformers(
            method_diff=sink,
            endpoint_diff=dummy_sink,
            contract_properties_diff=dummy_sink,
            contract_diff=dummy_sink
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            route_to_transformers.send(diff)
        
        results = [result[2][0][0] for result in results]
        route_to_transformers.close()
        
        assert len(results) == 2
        assert 'get' in results
        assert 'delete' in results
    
    def test_contracts_route_to_transformers_method(self, sink_factory,
                                                    swagger_file_diffs_pipeline):
        sink, results = sink_factory()
        dummy_sink, _ = sink_factory()
        
        route_to_transformers = swagger_file_diffs_pipeline.route_to_transformers(
            contract_diff=sink,
            method_diff=dummy_sink,
            endpoint_diff=dummy_sink,
            contract_properties_diff=dummy_sink
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            route_to_transformers.send(diff)
        
        results = [result[2][0][0] for result in results]
        route_to_transformers.close()
        
        assert len(results) == 2
        assert 'Category' in results
        assert 'subCategory' in results
    
    def test_contract_props_route_to_transformers_method(self, sink_factory,
                                                         swagger_file_diffs_pipeline):
        sink, results = sink_factory()
        dummy_sink, _ = sink_factory()
        
        route_to_transformers = swagger_file_diffs_pipeline.route_to_transformers(
            contract_properties_diff=sink,
            contract_diff=dummy_sink,
            method_diff=dummy_sink,
            endpoint_diff=dummy_sink
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            route_to_transformers.send(diff)
        
        results = [result[2][0][0] for result in results]
        route_to_transformers.close()
        
        assert len(results) == 4
        assert 'tags' in results
        assert 'subCategory' in results
        assert 'username' in results
        assert 'address' in results
    
    def test_endpoint_diff_transformer_method(self, sink_factory,
                                              swagger_file_diffs_pipeline):
        sink, results = sink_factory()
        dummy_sink, _ = sink_factory()
        
        endpoint_diff_transformer = \
            swagger_file_diffs_pipeline.endpoint_diff_transformer(sink)
        
        route_to_transformers = swagger_file_diffs_pipeline.route_to_transformers(
            endpoint_diff=endpoint_diff_transformer,
            contract_diff=dummy_sink,
            method_diff=dummy_sink,
            contract_properties_diff=dummy_sink
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            route_to_transformers.send(diff)
        
        results = [result['what'][0] for result in results]
        endpoint_diff_transformer.close()
        route_to_transformers.close()
        
        assert len(results) == 2
        assert '/pet/{petId}/uploadImage' in results
        assert '/pet/{petId}/uploadFile' in results
    
    def test_method_diff_transformer_method(self, sink_factory,
                                            swagger_file_diffs_pipeline):
        sink, results = sink_factory()
        dummy_sink, _ = sink_factory()
        
        method_diff_transformer = \
            swagger_file_diffs_pipeline.method_diff_transformer(sink)
        
        route_to_transformers = swagger_file_diffs_pipeline.route_to_transformers(
            method_diff=method_diff_transformer,
            contract_diff=dummy_sink,
            endpoint_diff=dummy_sink,
            contract_properties_diff=dummy_sink
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            route_to_transformers.send(diff)
        
        results = [(result['where'], result['what'][0]) for result in results]
        method_diff_transformer.close()
        route_to_transformers.close()
        
        assert len(results) == 2
        assert ('/pet', 'get') in results
        assert ('/pet/{petId}', 'delete') in results
    
    def test_contract_diff_transformer_method(self, sink_factory,
                                              swagger_file_diffs_pipeline):
        sink, results = sink_factory()
        dummy_sink, _ = sink_factory()
        
        contract_diff_transformer = \
            swagger_file_diffs_pipeline.contract_diff_transformer(sink)
        
        route_to_transformers = swagger_file_diffs_pipeline.route_to_transformers(
            contract_diff=contract_diff_transformer,
            method_diff=dummy_sink,
            endpoint_diff=dummy_sink,
            contract_properties_diff=dummy_sink
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            route_to_transformers.send(diff)
        
        results = [result['what'] for result in results]
        contract_diff_transformer.close()
        route_to_transformers.close()
        
        assert len(results) == 2
        assert ['Category', 'Tag'] in results
        assert ['subCategory'] in results
    
    def test_contract_properties_diff_transformer_method(self, sink_factory,
                                                         precalculated_results,
                                                         swagger_file_diffs_pipeline):
        sink, results = sink_factory()
        dummy_sink, _ = sink_factory()
        
        contract_properties_diff_transformer = \
            swagger_file_diffs_pipeline.contract_properties_diff_transformer(sink)
        
        route_to_transformers = swagger_file_diffs_pipeline.route_to_transformers(
            contract_properties_diff=contract_properties_diff_transformer,
            contract_diff=dummy_sink,
            method_diff=dummy_sink,
            endpoint_diff=dummy_sink,
        )
        
        for diff in dictdiffer.diff(
            swagger_file_diffs_pipeline.current_swagger_file_version,
            swagger_file_diffs_pipeline.new_swagger_file_version
        ):
            route_to_transformers.send(diff)
        
        contract_properties_diff_transformer.close()
        route_to_transformers.close()
        
        assert results == precalculated_results['contract_prop_diffs']
    
    def test_complete_pipeline_flow_and_results(self, precalculated_results,
                                                swagger_file_diffs_pipeline):
        swagger_file_diffs_pipeline.run()
        assert (swagger_file_diffs_pipeline.swagger_file_changes ==
                precalculated_results['pipeline_results'])

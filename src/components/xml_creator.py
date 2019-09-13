


class XmlCreator:

    # An xml parametrized sting
    parametrized_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <flow xmlns="urn:opendaylight:flow:inventory">
            <flow-name>{name}</flow-name>
            <id>{id}</id>
            <table_id>{table_id}</table_id>
            <priority>{priority}</priority>
            <instructions>
                <instruction>
                    <order>0</order>
                    <apply-actions>
                        <action>
                            <order>0</order>
                            <output-action>
                                <output-node-connector>{output_port}</output-node-connector>
                                <max-length>65535</max-length>
                            </output-action>
                        </action>
                    </apply-actions>
                </instruction>
            </instructions>
            <match>
                <ethernet-match>
                    <ethernet-type>
                        <type>2048</type>
                    </ethernet-type>
                    <ethernet-destination>
                        <address>{mac_dst}</address>
                    </ethernet-destination>
                </ethernet-match>
            </match>
        </flow>
    '''

    def crete_port_forward_flow(self, flow_id, output_port, mac_dst, flow_name='', table_id=0, priority=2000):
        if len(flow_name) == 0:
            self.flow_name = 'flow_' + flow_id

        return self.parametrized_xml.format(
                name = flow_name, 
                id = flow_id,
                table_id = table_id, 
                priority = priority, 
                output_port = output_port,
                mac_dst = mac_dst
            )    